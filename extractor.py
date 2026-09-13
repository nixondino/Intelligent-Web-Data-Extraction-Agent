import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from crawler import crawl_website


# -----------------------------
# 1. Initialize LLM
# -----------------------------

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)


# -----------------------------
# 2. JSON Parser
# -----------------------------

parser = JsonOutputParser()


# -----------------------------
# 3. Prompt
# -----------------------------

prompt = PromptTemplate(
    template="""
You are an intelligent web data extraction agent.

Analyze the webpage content and extract:

- title
- author
- date
- summary
- category
- source_url

Rules:
- Use only information available in the webpage.
- If information is unavailable, use null.
- Do not invent information.
- Keep the summary short.
- Return ONLY valid JSON.

{format_instructions}

Webpage URL:
{url}

Webpage content:
{webpage_text}
""",
    input_variables=["url", "webpage_text"],
    partial_variables={
        "format_instructions": parser.get_format_instructions()
    }
)


# -----------------------------
# 4. Pipeline Execution
# -----------------------------

if __name__ == "__main__":
    url = input("Enter website URL: ")

    print("\nCrawling website...")
    webpage_text = crawl_website(url)

    chain = prompt | llm | parser

    print("Extracting information...")
    result = chain.invoke({
        "url": url,
        "webpage_text": webpage_text
    })

    print("\n==============================")
    print("EXTRACTED DATA")
    print("==============================")
    print(result)