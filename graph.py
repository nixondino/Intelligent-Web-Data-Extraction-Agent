import os
import json
import re
from typing import TypedDict, Any, Dict, List, Optional

from langgraph.graph import StateGraph, START, END

from crawler import crawl_website, CrawlError
from cleaner import clean_dict, clean_data
from reporter import save_reports

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

# ==============================
# LLM INITIALIZATION
# ==============================

primary_llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

fallback_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

llm = primary_llm.with_fallbacks([fallback_llm])



# ==============================
# RESILIENT JSON PARSER & REPAIR
# ==============================

def repair_and_parse_json(content: str) -> dict:
    """
    Extracts and parses JSON from raw LLM output, handling markdown fences,
    trailing commas, single quotes, and partial/malformed text.
    """
    if not isinstance(content, str):
        raise ValueError("LLM response content must be a string.")

    text = content.strip()

    # 1. Remove Markdown code blocks
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text).strip()

    # 2. Extract substring between the first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or start >= end:
        raise ValueError(f"No JSON object delimiter found in model response: {text[:200]}")

    candidate = text[start:end + 1].strip()

    # 3. Direct parse attempt
    try:
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 4. Repair: Fix trailing commas in objects and arrays
    repaired = re.sub(r",\s*([\]}])", r"\1", candidate)

    # Fix unescaped newlines in multi-line string values
    try:
        data = json.loads(repaired)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 5. Fallback: Clean control characters and try again
    repaired_clean = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", repaired)
    try:
        data = json.loads(repaired_clean)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError as err:
        raise ValueError(f"Failed to parse valid JSON from LLM: {str(err)}\nSnippet: {candidate[:300]}")


def call_llm_safely(chain, inputs: dict) -> str:
    """
    Invokes a LangChain chain with Groq-specific exception handling,
    specifically detecting rate limits (HTTP 429).
    """
    try:
        response = chain.invoke(inputs)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "rate_limit" in err_str.lower() or "rate limit" in err_str.lower():
            raise RuntimeError("Groq API rate limit reached. Please try again later.")
        elif "authentication" in err_str.lower() or "invalid api key" in err_str.lower():
            raise RuntimeError("Invalid Groq API key. Please check your GROQ_API_KEY environment variable.")
        else:
            raise RuntimeError(f"Groq LLM service error: {err_str}")


# ==============================
# 1. DEFINE AGENT STATE
# ==============================

class AgentState(TypedDict):
    url: str
    plan: dict
    raw_html: str
    extracted_data: dict
    cleaned_data: dict
    summary: str
    report_path: str
    retry_count: int


# ==============================
# 2. CRAWLER NODE
# ==============================

def crawler_node(state: AgentState):
    print(f"\n[CRAWLER] Crawling website: {state['url']}")

    try:
        webpage_text = crawl_website(state["url"])
    except CrawlError as ce:
        print(f"[CRAWLER] CrawlError: {ce}")
        raise ce
    except Exception as e:
        print(f"[CRAWLER] Unexpected crawling failure: {e}")
        raise CrawlError("CRAWL_FAILED", str(e))

    return {
        "raw_html": webpage_text,
        "retry_count": state.get("retry_count", 0) + 1
    }


# ==============================
# 3. VALIDATOR NODE & ROUTER
# ==============================

def validator_node(state: AgentState):
    print("[VALIDATOR] Validating retrieved content...")
    webpage_text = state.get("raw_html", "")

    if not webpage_text or len(webpage_text.strip()) < 80:
        print("[VALIDATOR] Warning: Content is empty or too short.")
        return {"raw_html": ""}

    print(f"[VALIDATOR] Content is usable ({len(webpage_text)} chars).")
    return {"raw_html": webpage_text}


def validation_router(state: AgentState):
    webpage_text = state.get("raw_html", "")
    retry_count = state.get("retry_count", 0)

    if webpage_text and len(webpage_text.strip()) >= 80:
        print("[ROUTER] Content validated -> Proceeding to Planner.")
        return "planner"

    if retry_count < 2:
        print(f"[ROUTER] Content invalid, retry attempt {retry_count + 1} -> Crawler.")
        return "retry"

    print("[ROUTER] Max retries exhausted with unusable content -> End.")
    return "end"


# ==============================
# 4. PLANNER NODE
# ==============================

PLANNER_PROMPT_TEMPLATE = """
You are an intelligent web data extraction planner.
Analyze the target webpage content and construct a dynamic, highly relevant extraction plan.

Return ONLY a single valid JSON object. No intro, no conversational text, no markdown fences.

Required JSON Structure:
{{
    "page_type": "article | news | blog | directory | product | research paper | documentation | other",
    "extraction_goal": "Concise statement of the information to extract from this specific webpage",
    "fields": ["field1", "field2", "field3", ...],
    "strategy": "Brief strategy for semantic extraction"
}}

Strict Domain Rules:
1. Dynamic Adaptation: Choose fields that actually exist on this webpage. Do NOT use a rigid static list.
2. News & Articles: Consider title, author, date, summary, category, key_takeaways, source_url.
3. Business Directories: Consider business_name, category, address, location, phone, email, website, rating, services, description, source_url.
4. Research Papers: Consider title, authors, publication_date, abstract, journal, conference, doi, keywords, findings, source_url.
5. Products: Consider product_name, price, brand, rating, specifications, availability, description, source_url.
6. MANDATORY FIELDS (Must always be included in the 'fields' list):
   - "source_url"
   - "summary"

Target URL:
{url}

Webpage Content Preview:
{webpage_text}
"""

planner_prompt = PromptTemplate(
    template=PLANNER_PROMPT_TEMPLATE,
    input_variables=["url", "webpage_text"]
)

planner_chain = planner_prompt | llm


def planner_node(state: AgentState):
    print("[PLANNER] Analyzing content and formulating dynamic schema plan...")

    # Send up to 6,000 characters of token-optimized content
    content_slice = state["raw_html"][:6000]

    raw_output = call_llm_safely(planner_chain, {
        "url": state["url"],
        "webpage_text": content_slice
    })

    plan = repair_and_parse_json(raw_output)

    # Ensure required structure
    if not isinstance(plan.get("fields"), list):
        plan["fields"] = []

    # Guarantee mandatory fields
    if "source_url" not in plan["fields"]:
        plan["fields"].append("source_url")
    if "summary" not in plan["fields"]:
        plan["fields"].append("summary")

    if not plan.get("page_type"):
        plan["page_type"] = "Web Page"
    if not plan.get("extraction_goal"):
        plan["extraction_goal"] = "Extract key intelligence from webpage."

    print(f"[PLANNER] Classified as '{plan.get('page_type')}'. Planned fields: {plan.get('fields')}")

    return {
        "plan": plan
    }


# ==============================
# 5. EXTRACTOR NODE
# ==============================

EXTRACTOR_PROMPT_TEMPLATE = """
You are a precision web data extraction agent.
Extract information from the webpage strictly according to the provided schema plan.

Extraction Plan:
- Page Type: {page_type}
- Goal: {goal}
- Planned Fields: {fields_list}

Webpage URL:
{url}

Webpage Content:
{webpage_text}

Rules:
1. Return exactly ONE valid JSON object with keys matching the Planned Fields.
2. If a field cannot be found or is not applicable, set its value to null.
3. Never invent, hallucinate, or assume facts not present in the content.
4. For list fields (like authors, keywords, categories, specifications), return a clean JSON array of strings or objects.
5. Keep the "summary" field concise (2-4 sentences) summarizing the main information.
6. The "source_url" field MUST equal "{url}".
7. Return ONLY valid JSON. No conversational preamble, no markdown formatting.
"""

extractor_prompt = PromptTemplate(
    template=EXTRACTOR_PROMPT_TEMPLATE,
    input_variables=["page_type", "goal", "fields_list", "url", "webpage_text"]
)

extractor_chain = extractor_prompt | llm


def extractor_node(state: AgentState):
    print("[EXTRACTOR] Performing semantic data extraction...")

    plan = state.get("plan", {})
    fields = plan.get("fields", ["title", "summary", "source_url"])
    page_type = plan.get("page_type", "General")
    goal = plan.get("extraction_goal", "Extract structured information.")

    # Pass up to 7,500 characters of token-optimized content
    content_slice = state["raw_html"][:7500]

    raw_output = call_llm_safely(extractor_chain, {
        "page_type": page_type,
        "goal": goal,
        "fields_list": ", ".join(fields),
        "url": state["url"],
        "webpage_text": content_slice
    })

    extracted = repair_and_parse_json(raw_output)

    # Guarantee all planned fields exist (fill missing with None)
    for field in fields:
        if field not in extracted:
            extracted[field] = None

    # Always enforce source_url
    extracted["source_url"] = state["url"]

    # If summary is missing or null, provide a synthesized fallback from title
    if not extracted.get("summary"):
        title_val = extracted.get("title") or "the webpage"
        extracted["summary"] = f"Extracted structured content from {title_val}."

    print(f"[EXTRACTOR] Extracted {len(extracted)} structured fields successfully.")

    return {
        "extracted_data": extracted
    }


# ==============================
# 6. CLEANER NODE
# ==============================

def cleaner_node(state: AgentState):
    print("[CLEANER] Sanitizing and normalizing data...")

    extracted = state.get("extracted_data", {})
    cleaned_dict_data = clean_dict(extracted)

    # Sync summary
    summary_val = str(cleaned_dict_data.get("summary") or "")

    return {
        "cleaned_data": cleaned_dict_data,
        "summary": summary_val
    }


# ==============================
# 7. REPORTER NODE
# ==============================

def reporter_node(state: AgentState):
    print("[REPORTER] Generating CSV, JSON, and PDF reports...")

    plan = state.get("plan", {})
    page_type = plan.get("page_type", "Web Page")
    cleaned_data = state.get("cleaned_data", {})

    csv_path, json_path, pdf_path = save_reports(
        data=cleaned_data,
        output_folder="output",
        page_type=page_type,
        plan=plan
    )

    print(f"[REPORTER] Reports created: {csv_path}, {json_path}, {pdf_path}")

    return {
        "report_path": f"{csv_path}, {json_path}, {pdf_path}"
    }


# ==============================
# 8. ASSEMBLE LANGGRAPH
# ==============================

graph_builder = StateGraph(AgentState)

# Add all nodes
graph_builder.add_node("crawler", crawler_node)
graph_builder.add_node("validator", validator_node)
graph_builder.add_node("planner", planner_node)
graph_builder.add_node("extractor", extractor_node)
graph_builder.add_node("cleaner", cleaner_node)
graph_builder.add_node("reporter", reporter_node)

# Flow: START -> crawler -> validator -> (planner | retry | END)
graph_builder.add_edge(START, "crawler")
graph_builder.add_edge("crawler", "validator")

graph_builder.add_conditional_edges(
    "validator",
    validation_router,
    {
        "planner": "planner",
        "retry": "crawler",
        "end": END
    }
)

# Linear flow after validation: planner -> extractor -> cleaner -> reporter -> END
graph_builder.add_edge("planner", "extractor")
graph_builder.add_edge("extractor", "cleaner")
graph_builder.add_edge("cleaner", "reporter")
graph_builder.add_edge("reporter", END)

# Compile graph
graph = graph_builder.compile()


# ==============================
# CLI TEST RUNNER
# ==============================

if __name__ == "__main__":
    target_url = input("Enter website URL: ")

    initial_state = {
        "url": target_url,
        "plan": {},
        "raw_html": "",
        "extracted_data": {},
        "cleaned_data": {},
        "summary": "",
        "report_path": "",
        "retry_count": 0
    }

    try:
        print("\nStarting execution graph...")
        for event in graph.stream(initial_state):
            for node_name, output in event.items():
                print(f"-> Node '{node_name}' finished.")
        print("\nPipeline execution complete!")
    except Exception as e:
        print(f"\nExecution error: {e}")