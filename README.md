# Intelligent Web Data Extraction Agent

An autonomous, production-grade AI web intelligence system that dynamically crawls, analyzes, plans, extracts, cleans, and exports structured datasets from any webpage.

Built with **LangGraph**, **LangChain**, **Groq AI** (`openai/gpt-oss-20b`), **Playwright**, **Pandas**, and **ReportLab**, featuring a modern **Streamlit** user interface.

---

## 1. Project Overview

Traditional web scraping scripts rely on brittle, hard-coded CSS or XPath selectors that break whenever a website updates its HTML markup. Furthermore, extracting data across diverse domains—ranging from tech blogs and e-commerce stores to business directories and academic portals—previously required writing bespoke scrapers for each layout.

The **Intelligent Web Data Extraction Agent** solves this through autonomous reasoning:
1. **Headless Browser Execution**: Uses Playwright to render modern JavaScript-heavy websites with realistic desktop emulation.
2. **Semantic DOM Sanitization**: Aggressively strips scripts, stylesheets, ads, navbars, and cookie banners to reduce Groq LLM token consumption while preserving high-signal content.
3. **Dynamic Schema Planning**: The AI Planner analyzes the webpage's structure and semantics to dynamically deduce the page classification and target schema fields.
4. **Precision Extraction & JSON Repair**: The AI Extractor populates the schema strictly from the observed content without hallucination, with an automated JSON repair engine.
5. **Safe Data Cleaning**: Normalizes whitespace, cleans text, and safely handles nested structures without corrupting URLs, DOIs, or email addresses.
6. **Multi-Format Exporting**: Produces machine-readable JSON, tabular CSV, and executive PDF reports with clear formatting for nested data structures.

---

## 2. Architecture & Pipeline

The agent executes as a stateful, cyclical computation graph orchestrated by **LangGraph**:

```
                  ┌─────────────────┐
                  │   Target URL    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Crawler Node   │◄────────┐
                  │  (Playwright)   │         │
                  └────────┬────────┘         │
                           │                  │ (Retry < 2)
                           ▼                  │
                  ┌─────────────────┐         │
                  │ Validator Node  ├─────────┘
                  │  (DOM Check)    ├─────────┐
                  └────────┬────────┘         │ (Invalid / Max retries)
                           │ (Valid)          ▼
                           ▼            ┌───────────┐
                  ┌─────────────────┐   │    END    │
                  │  Planner Node   │   │  (Error)  │
                  │   (Schema AI)   │   └───────────┘
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Extractor Node  │
                  │ (LLM Synthesis) │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Cleaner Node   │
                  │ (Normalization) │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Reporter Node  │
                  │ (CSV, JSON, PDF)│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │       END       │
                  │ (UI Completed)  │
                  └─────────────────┘
```

### State Graph Flow
1. **START → Crawler**: Launches headless Chromium with realistic user-agent headers and fetches full page HTML.
2. **Crawler → Validator**: Assesses content quality (minimum 80 characters of clean readable text).
3. **Conditional Branch (`validation_router`)**:
   - `len(text) >= 80` ➔ Routes to **Planner**.
   - `len(text) < 80` and `retries < 2` ➔ Re-routes to **Crawler** for a retry attempt.
   - `retries >= 2` ➔ Terminates cleanly at **END** with an informative error state.
4. **Planner → Extractor**: Hands off the dynamic schema plan (`page_type`, `fields`, `extraction_goal`, `strategy`).
5. **Extractor → Cleaner**: Sanitizes values and handles nested lists/objects without type coercion errors.
6. **Cleaner → Reporter**: Saves the cleaned records into `output/extracted_data.csv`, `output/extracted_data.json`, and `output/extracted_report.pdf`.
7. **Reporter → END**: Delivers final state to Streamlit for real-time visualization.

---

## 3. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Agent Orchestration** | LangGraph (v1.x) | Cyclic state graph, conditional edges, retry routing |
| **LLM Framework** | LangChain Core | Prompt engineering, chain construction |
| **Inference Engine** | Groq (`openai/gpt-oss-20b`) | Ultra-fast semantic reasoning, schema formulation |
| **Web Crawling** | Playwright (Python Sync) | Full JavaScript rendering, anti-detection flags |
| **HTML Parsing** | BeautifulSoup4 | Semantic DOM tree cleaning, token reduction |
| **Data Processing** | Pandas | Structured dataset manipulation, CSV formatting |
| **Document Generation** | ReportLab | Flowable executive PDF reports with nested styling |
| **Frontend UI** | Streamlit | Modern SaaS interface, live streaming status |
| **Environment** | python-dotenv | Local credential management |

---

## 4. Key Agent Components

### 4.1 Crawler (`crawler.py`)
- **Desktop Emulation**: Overrides default headless signatures with a modern Chrome Windows User-Agent, custom viewport, and accepted headers to prevent 403 Forbidden blocks.
- **Robust Error Classification**: Detects DNS failures (`net::ERR_NAME_NOT_RESOLVED`), connection timeouts, server errors (5xx), and client blocks (403/404), converting them into typed `CrawlError` instances.
- **Token-Optimized DOM Cleaning**: Decomposes `<script>`, `<style>`, `<nav>`, `<footer>`, `<aside>`, cookie notices, and advertisements. Automatically pinpoints `<article>`, `<main>`, or `.content` tags, truncating cleanly to a token-efficient threshold (~8,000 characters).

### 4.2 Planner (`graph.py`)
- Analyzes the preprocessed content and determines the specific domain type (`news`, `directory`, `research paper`, `product`, `documentation`).
- Dynamically selects fields relevant to the detected content instead of forcing a rigid static schema.
- Enforces mandatory fields across all extractions: `source_url` and `summary`.

### 4.3 Extractor (`graph.py`)
- Follows the Planner's requested fields strictly.
- Enforces a zero-hallucination policy (`null` for any field not explicitly present in the source).
- Employs a multi-stage **JSON Repair Engine**:
  - Strips markdown code fences (` ```json `).
  - Isolates matching outer JSON delimiters (`{ ... }`).
  - Corrects trailing commas in objects and arrays.
  - Sanitizes unescaped control characters.

### 4.4 Cleaner (`cleaner.py`)
- Recursively cleans primitive values and nested collections (lists, tuples, dictionaries).
- Protects URLs, emails, DOIs, and numerical versions from regex splitting bugs.
- Preserves `None` across objects without converting to unparseable `NaN` values.

### 4.5 Reporter (`reporter.py`)
- **JSON**: Produces clean UTF-8 formatted JSON.
- **CSV**: Flattens nested lists/dictionaries into clean stringified columns readable by Excel or Pandas.
- **PDF**: Uses ReportLab to generate an executive-ready document containing:
  - Project Title & Metadata Banner
  - Target URL & Extraction Timestamp
  - Page Classification Badge
  - Highlighted Executive Summary Box
  - Extracted Data Table with bulleted sub-formatting for nested lists and dictionaries.

---

## 5. Supported Use Cases

### 1. Technology & News Articles
- **Target Pages**: TechCrunch, Hacker News, Python Blogs, BBC Tech.
- **Dynamic Fields**: `title`, `author`, `date`, `summary`, `category`, `key_takeaways`, `source_url`.
- **Value**: Captures article text, bylines, publication timestamps, and executive summaries without sidebar clutter.

### 2. Business Directories & Local Listings
- **Target Pages**: Yelp, YellowPages, Chamber of Commerce directories.
- **Dynamic Fields**: `business_name`, `category`, `address`, `location`, `phone`, `email`, `website`, `rating`, `services`, `description`, `source_url`.
- **Value**: Extracts contact points, addresses, and service listings into exportable CSV datasets.

### 3. Academic Research Papers
- **Target Pages**: arXiv, PubMed, IEEE Xplore, Google Scholar.
- **Dynamic Fields**: `title`, `authors`, `publication_date`, `abstract`, `journal`, `conference`, `doi`, `keywords`, `findings`, `source_url`.
- **Value**: Parses complex academic metadata, multi-author arrays, DOIs, and scientific summaries.

### 4. E-Commerce & Documentation
- **Target Pages**: Product catalogs, API documentation, developer guides.
- **Dynamic Fields**: `product_name`, `price`, `brand`, `specifications`, `documentation_topic`, `overview`, `source_url`.

---

## 6. Installation & Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Playwright browser binaries
- Groq Cloud API Key

### Step 1: Clone Repository
```bash
git clone <repository_url>
cd intelligent-web-data-agent
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies & Playwright Browsers
```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 4: Configure API Keys
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

---

## 7. How to Run

### Option A: Launch Interactive Web Application (Recommended)
```powershell
# Directly using the virtual environment executable:
.\venv\Scripts\streamlit.exe run app.py

# Or within an activated environment:
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Option B: Run via CLI Test Mode
```powershell
.\venv\Scripts\python.exe graph.py
```

### Option C: Run Automated Validation Test Suite
```powershell
.\venv\Scripts\python.exe run_pipeline_tests.py
```

---

## 8. Error Handling & Resilience Matrix

| Error Scenario | Detection Mechanism | System Behavior |
| :--- | :--- | :--- |
| **Invalid URL** | `normalize_url` validation | Displays clear URL formatting alert card; halts before crawler. |
| **DNS Resolution Failure** | Playwright network error trap | Catches `ERR_NAME_NOT_RESOLVED`; shows "Domain Not Found" card. |
| **HTTP 403 Forbidden** | Playwright response status | Identifies anti-bot block; displays "Access Denied" guidance. |
| **HTTP 404 Not Found** | Playwright response status | Captures missing URL; displays "Page Not Found (404)" message. |
| **Request Timeout** | 25s Playwright timeout trap | Aborts hung connections gracefully; reports slow server response. |
| **Empty / Blocked Page** | `< 80` readable characters | Validator rejects empty content; triggers 1 retry before clean stop. |
| **Groq 429 Rate Limit** | LLM exception handler | Displays: *"Groq API rate limit reached. Please try again later."* |
| **Malformed LLM JSON** | `repair_and_parse_json` | Strips code fences, removes trailing commas, repairs control chars. |
| **Missing Fields** | Schema validator | Automatically backfills any unextracted fields with `null`. |
| **Unhashable Data Types** | `cleaner.py` recursive logic | Safely normalizes nested dicts/lists without pandas hashing crashes. |

---

## 9. Project Limitations & Future Roadmap

### Current Limitations
1. **CAPTCHA & Cloudflare Turnstile**: Sites with active JavaScript Turnstile challenges or puzzle captchas cannot be bypassed without specialized proxy services.
2. **Authentication Walls**: Requires public accessibility; does not crawl pages requiring multi-factor authentication or single-sign-on (SSO).
3. **Multi-Page Pagination**: Operates on single URL targets per extraction run.

### Future Roadmap
- [ ] Multi-page recursive crawling for deep domain scraping.
- [ ] Visual multimodal extraction utilizing screenshots alongside DOM text.
- [ ] Webhook and cloud database export integrations (PostgreSQL, BigQuery).
- [ ] Configurable proxy pool rotation for enterprise-scale crawling.

---

## 10. Confidentiality & License

This project was developed as a proprietary intelligent data extraction agent. All code, architecture designs, and models are intended for authorized demonstration and internal evaluation. Do not distribute or publish to public code repositories without permission.
