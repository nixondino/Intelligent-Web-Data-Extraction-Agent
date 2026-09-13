import os
import json
import streamlit as st
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

from graph import graph


# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Intelligent Web Data Extraction Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==============================================================================
# CUSTOM CSS / MODERN AI SAAS DESIGN SYSTEM
# ==============================================================================

CUSTOM_CSS = """
<style>
/* Import Modern Typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-main: #07090e;
    --bg-card: rgba(15, 23, 42, 0.72);
    --bg-card-hover: rgba(30, 41, 59, 0.85);
    --border-card: rgba(255, 255, 255, 0.08);
    --border-glow: rgba(59, 130, 246, 0.25);
    --accent-cyan: #06b6d4;
    --accent-blue: #3b82f6;
    --accent-indigo: #6366f1;
    --accent-purple: #8b5cf6;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

/* Base Body & App Styling */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
}

.stApp {
    background-color: var(--bg-main);
    background-image: 
        radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.06) 0%, transparent 45%),
        radial-gradient(circle at 85% 20%, rgba(139, 92, 246, 0.06) 0%, transparent 45%),
        radial-gradient(circle at 50% 80%, rgba(6, 182, 212, 0.04) 0%, transparent 50%);
    background-attachment: fixed;
}

/* Clean Header & Navigation Bar */
.top-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 2rem;
    margin-bottom: 2rem;
    background: rgba(11, 15, 25, 0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-card);
    border-radius: 16px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.brand-icon-wrapper {
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
    border: 1px solid rgba(59, 130, 246, 0.35);
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);
    font-size: 1.35rem;
}

.brand-title {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #ffffff;
    margin: 0;
    line-height: 1.2;
}

.brand-subtitle {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin: 0;
    font-weight: 400;
    letter-spacing: 0.01em;
}

.status-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #34d399;
    letter-spacing: 0.03em;
}

.status-dot {
    width: 7px;
    height: 7px;
    background-color: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 8px #10b981;
    animation: pulse-glow 2s infinite ease-in-out;
}

@keyframes pulse-glow {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
}

/* Hero Section */
.hero-wrapper {
    text-align: center;
    max-width: 820px;
    margin: 0 auto 2.5rem auto;
    padding: 1rem 0;
}

.hero-title {
    font-size: 2.75rem;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.03em;
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, #ffffff 30%, #93c5fd 70%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.05rem;
    line-height: 1.6;
    color: var(--text-secondary);
    max-width: 650px;
    margin: 0 auto;
    font-weight: 400;
}

/* Glassmorphism Card Container */
.saas-card {
    background: var(--bg-card);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--border-card);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 30px -4px rgba(0, 0, 0, 0.4);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.saas-card:hover {
    border-color: rgba(255, 255, 255, 0.12);
}

.card-header-flex {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.15rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    letter-spacing: -0.01em;
    margin: 0;
}

/* Section Subheaders */
.section-heading {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.95rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent-cyan);
    margin-bottom: 1rem;
}

/* Pipeline Flow Layout */
.pipeline-container {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0.75rem;
    margin-bottom: 2rem;
}

@media (max-width: 1024px) {
    .pipeline-container {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 640px) {
    .pipeline-container {
        grid-template-columns: repeat(2, 1fr);
    }
}

.pipe-step-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(8px);
    border: 1px solid var(--border-card);
    border-radius: 12px;
    padding: 1rem 0.75rem;
    text-align: center;
    position: relative;
    transition: all 0.25s ease;
}

.pipe-step-card.waiting {
    opacity: 0.65;
    border-color: rgba(255, 255, 255, 0.05);
}

.pipe-step-card.running {
    opacity: 1;
    border-color: var(--accent-cyan);
    background: rgba(6, 182, 212, 0.08);
    box-shadow: 0 0 20px -3px rgba(6, 182, 212, 0.35);
    transform: translateY(-2px);
}

.pipe-step-card.completed {
    opacity: 1;
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(16, 185, 129, 0.06);
    box-shadow: 0 0 15px -3px rgba(16, 185, 129, 0.2);
}

.pipe-icon {
    font-size: 1.5rem;
    margin-bottom: 0.4rem;
    display: inline-block;
}

.pipe-name {
    font-size: 0.85rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.3rem;
}

.pipe-desc {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-bottom: 0.6rem;
    line-height: 1.2;
}

.pipe-badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.badge-waiting {
    background: rgba(100, 116, 139, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(100, 116, 139, 0.2);
}

.badge-running {
    background: rgba(6, 182, 212, 0.2);
    color: #67e8f9;
    border: 1px solid rgba(6, 182, 212, 0.4);
    animation: pulse-glow 1.5s infinite;
}

.badge-completed {
    background: rgba(16, 185, 129, 0.2);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

/* Badge Chips for Fields */
.field-chip {
    display: inline-flex;
    align-items: center;
    background: rgba(59, 130, 246, 0.1);
    color: #93c5fd;
    border: 1px solid rgba(59, 130, 246, 0.25);
    border-radius: 8px;
    padding: 0.25rem 0.65rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 500;
    margin: 0.2rem;
    letter-spacing: -0.01em;
}

.badge-pill {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
    border: 1px solid rgba(139, 92, 246, 0.35);
    color: #c4b5fd;
}

/* AI Summary Card Accent */
.summary-card {
    background: var(--bg-card);
    backdrop-filter: blur(14px);
    border: 1px solid var(--border-card);
    border-left: 4px solid var(--accent-purple);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 30px -4px rgba(0, 0, 0, 0.4);
}

.summary-text {
    font-size: 0.95rem;
    line-height: 1.7;
    color: #cbd5e1;
    margin: 0;
}

/* Report Download Cards */
.report-card {
    background: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-card);
    border-radius: 14px;
    padding: 1.25rem;
    text-align: center;
    transition: all 0.2s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.report-card:hover {
    border-color: rgba(255, 255, 255, 0.15);
    transform: translateY(-2px);
    box-shadow: 0 12px 28px -5px rgba(0, 0, 0, 0.5);
}

.report-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.report-title {
    font-size: 1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.25rem;
}

.report-desc {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-bottom: 1rem;
    line-height: 1.4;
}

/* Key-Value Structured Display */
.kv-row {
    display: flex;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    align-items: baseline;
    transition: background 0.15s ease;
}

.kv-row:last-child {
    border-bottom: none;
}

.kv-row:hover {
    background: rgba(255, 255, 255, 0.02);
}

.kv-key {
    width: 28%;
    min-width: 140px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent-cyan);
    word-break: break-word;
}

.kv-val {
    width: 72%;
    font-size: 0.875rem;
    color: #e2e8f0;
    line-height: 1.5;
    word-break: break-word;
}

/* Alert Styling */
.alert-card {
    background: rgba(244, 63, 94, 0.08);
    border: 1px solid rgba(244, 63, 94, 0.25);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
}

.alert-icon {
    font-size: 1.5rem;
    line-height: 1;
}

.alert-content {
    flex: 1;
}

.alert-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #fda4af;
    margin-bottom: 0.25rem;
}

.alert-message {
    font-size: 0.85rem;
    color: #fecdd3;
    line-height: 1.5;
    margin: 0;
}

/* Professional Footer */
.saas-footer {
    text-align: center;
    padding: 3rem 0 1.5rem 0;
    margin-top: 3rem;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    color: var(--text-muted);
    font-size: 0.8rem;
    letter-spacing: 0.02em;
}

.footer-tech {
    font-weight: 500;
    color: var(--text-secondary);
}

/* Override Streamlit Default Widget Styling */
div[data-testid="stTextInput"] > div > div {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-size: 0.95rem !important;
    padding: 0.25rem 0.5rem !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stTextInput"] > div > div:focus-within {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
}

div[data-testid="stButton"] > button {
    width: 100%;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 18px -2px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.2s ease !important;
    height: 48px !important;
}

div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px -2px rgba(99, 102, 241, 0.6) !important;
    filter: brightness(1.08) !important;
}

div[data-testid="stDownloadButton"] > button {
    width: 100%;
    background: rgba(30, 41, 59, 0.8) !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    padding: 0.55rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stDownloadButton"] > button:hover {
    background: rgba(51, 65, 85, 0.95) !important;
    border-color: var(--accent-blue) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(59, 130, 246, 0.25) !important;
}

/* Streamlit Tabs */
div[data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 1rem !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding-bottom: 0.25rem !important;
}

div[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
}

div[data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent-cyan) !important;
    border-bottom: 2px solid var(--accent-cyan) !important;
}

/* Hide Streamlit Branding Clutter */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# PIPELINE CONFIGURATION & HTML RENDERER
# ==============================================================================




# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

if "result" not in st.session_state:
    st.session_state.result = None

if "completed_stages" not in st.session_state:
    st.session_state.completed_stages = []

if "error_info" not in st.session_state:
    st.session_state.error_info = None

if "current_url" not in st.session_state:
    st.session_state.current_url = ""


# ==============================================================================
# 1. TOP NAVIGATION / HEADER
# ==============================================================================

st.markdown("""
<div class="top-navbar">
    <div class="nav-brand">
        <div class="brand-icon-wrapper">⚡</div>
        <div>
            <div class="brand-title">Intelligent Web Data Extraction Agent</div>
            <div class="brand-subtitle">Autonomous AI-powered web intelligence</div>
        </div>
    </div>
    <div class="status-badge">
        <span class="status-dot"></span>
        <span>Agent Online</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. HERO SECTION & URL INPUT
# ==============================================================================

st.markdown("""
<div class="hero-wrapper">
    <div class="hero-title">Extract Intelligence From Any Website</div>
    <div class="hero-subtitle">
        Let an autonomous AI agent crawl, understand, extract, clean and organize web data with self-directed planning and validation.
    </div>
</div>
""", unsafe_allow_html=True)

# Search Input Container
input_col, button_col = st.columns([4, 1.2])

with input_col:
    url_input = st.text_input(
        "Website URL",
        value=st.session_state.current_url,
        placeholder="https://example.com or any news, article, product page...",
        label_visibility="collapsed"
    )

with button_col:
    start_btn = st.button("🚀 Start Extraction", use_container_width=True)


# ==============================================================================
# EXECUTION LOGIC (TRIGGERED BY BUTTON)
# ==============================================================================

if start_btn:
    cleaned_url = url_input.strip()

    if not cleaned_url:
        st.markdown("""
        <div class="alert-card">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
                <div class="alert-title">URL Required</div>
                <p class="alert-message">Please provide a valid website address before initiating the extraction pipeline.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Reset state for fresh run
        st.session_state.current_url = cleaned_url
        st.session_state.result = None
        st.session_state.error_info = None
        st.session_state.completed_stages = []

        initial_state = {
            "url": cleaned_url,
            "plan": {},
            "raw_html": "",
            "extracted_data": {},
            "cleaned_data": {},
            "summary": "",
            "report_path": "",
            "retry_count": 0
        }

        stage_labels = {
            "crawler": "🌐 Crawling webpage with Playwright...",
            "validator": "🛡 Validating DOM & content structure...",
            "planner": "🧠 Formulating extraction schema & targets...",
            "extractor": "🔍 Synthesizing semantic extraction with AI...",
            "cleaner": "🧹 Normalizing & validating data records...",
            "reporter": "📄 Compiling JSON, CSV & PDF export reports..."
        }

        completed = []
        result_collector = {}

        with st.status("⚡ Running autonomous extraction pipeline...", expanded=True) as status_box:
            try:
                for event in graph.stream(initial_state):
                    for node_name, node_output in event.items():
                        result_collector.update(node_output)
                        if node_name not in completed:
                            completed.append(node_name)
                        label = stage_labels.get(node_name, f"Completed {node_name}")
                        st.write(label)

                # Check if validator dropped execution early due to unusable content
                if not result_collector.get("cleaned_data") and not result_collector.get("plan"):
                    raise ValueError("The website content could not be validated or extracted. Please verify that the website allows public access and contains readable text.")

                # Finalize completed state
                st.session_state.result = result_collector
                st.session_state.completed_stages = completed
                status_box.update(label="✅ Extraction completed successfully!", state="complete", expanded=False)

            except Exception as e:
                st.session_state.error_info = str(e)
                st.session_state.completed_stages = completed
                status_box.update(label="❌ Pipeline stopped", state="error", expanded=True)


# ==============================================================================
# 8. ERROR HANDLING (DISPLAY CARD)
# ==============================================================================

if st.session_state.error_info:
    err = st.session_state.error_info

    if "rate limit" in err.lower() or "429" in err:
        title = "Rate Limit Exceeded"
        msg = "Groq API rate limit reached. Please try again later."
    elif "INVALID_URL" in err or "Invalid URL" in err:
        title = "Invalid URL"
        msg = "The provided website address is invalid. Please enter a complete, valid URL (e.g., https://example.com)."
    elif "DNS_FAILURE" in err or "ERR_NAME_NOT_RESOLVED" in err or "getaddrinfo" in err or "Domain could not be resolved" in err:
        title = "Domain Not Found"
        msg = "The specified website domain could not be resolved. Please verify the URL syntax and check your network connection."
    elif "TIMEOUT" in err or "Timeout" in err or "timeout" in err:
        title = "Request Timed Out"
        msg = "The target server took too long to respond (exceeded 25s). The website might be temporarily down or responding slowly."
    elif "HTTP_403" in err or "403" in err or "Access Denied" in err:
        title = "Access Denied (403 Forbidden)"
        msg = "The target website blocked crawler access. Cloudflare, anti-bot protection, or authentication is preventing automated extraction."
    elif "HTTP_404" in err or "404" in err:
        title = "Page Not Found (404)"
        msg = "The requested page was not found at this address. Please confirm the URL path."
    elif "EMPTY_CONTENT" in err or "empty or unparseable" in err.lower() or "Validator" in err or "content could not be validated" in err.lower():
        title = "Content Validation Failed"
        msg = "The page was retrieved, but contained no readable text content. The page might rely heavily on JavaScript authentication or cookie walls."
    elif "CONNECTION_REFUSED" in err:
        title = "Connection Refused"
        msg = "The target server actively refused the connection. Please confirm the host is currently accessible."
    else:
        title = "Extraction Pipeline Interrupted"
        msg = "An error occurred while processing the website. Please review technical trace details below."

    st.markdown(f"""
    <div class="alert-card">
        <div class="alert-icon">⚠️</div>
        <div class="alert-content">
            <div class="alert-title">{title}</div>
            <p class="alert-message">{msg}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Technical Trace Details"):
        st.code(err, language="text")


# ==============================================================================
# DISPLAY RESULTS WHEN AVAILABLE
# ==============================================================================

if st.session_state.result:
    res = st.session_state.result
    plan = res.get("plan", {})
    cleaned_data = res.get("cleaned_data", {})
    summary = res.get("summary", "")

    # Layout in 2 Columns: Extraction Plan & AI Summary
    plan_col, summary_col = st.columns([1.1, 1])

    # ==========================================================================
    # 4. EXTRACTION PLAN
    # ==========================================================================
    with plan_col:
        page_type = plan.get("page_type", "General Webpage").title() if isinstance(plan.get("page_type"), str) else "General"
        goal = plan.get("extraction_goal", "Extract key structured intelligence from page content.")
        fields = plan.get("fields", [])
        strategy = plan.get("strategy", "Dynamic semantic schema mapping based on document structure.")

        fields_badges = "".join([f'<span class="field-chip">#{f}</span>' for f in fields]) if fields else '<span style="color:#64748b;">No explicit fields mapped</span>'

        st.markdown(f"""
        <div class="saas-card" style="height: 100%;">
            <div class="card-header-flex">
                <div class="card-title">🧠 Autonomous Extraction Plan</div>
                <div class="badge-pill">{page_type}</div>
            </div>
            <div style="margin-bottom: 1rem;">
                <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.35rem;">Target Goal</div>
                <div style="font-size: 0.9rem; color: #f1f5f9; line-height: 1.5;">{goal}</div>
            </div>
            <div style="margin-bottom: 1rem;">
                <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.35rem;">Planned Schema Fields</div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">{fields_badges}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.35rem;">Execution Strategy</div>
                <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5; font-style: italic;">"{strategy}"</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================================================
    # 6. AI SUMMARY
    # ==========================================================================
    with summary_col:
        display_summary = summary if summary else "No synthesized summary was generated for this webpage."

        st.markdown(f"""
        <div class="summary-card" style="height: 100%;">
            <div class="card-header-flex">
                <div class="card-title">✨ AI Executive Summary</div>
                <span style="font-size: 0.75rem; color: #a78bfa; font-weight: 600;">Groq Synthesized</span>
            </div>
            <p class="summary-text">{display_summary}</p>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================================================
    # 5. EXTRACTED DATA (STRUCTURED & RAW JSON)
    # ==========================================================================
    st.markdown('<div class="section-heading" style="margin-top: 1.5rem;">🔍 Extracted Intelligence</div>', unsafe_allow_html=True)

    tab_structured, tab_json = st.tabs(["📊 Structured Dataset", "{} Raw JSON Inspector"])

    with tab_structured:
        if cleaned_data:
            # Separate primitives from complex nested data
            primitives = {}
            nested = {}

            for k, v in cleaned_data.items():
                if isinstance(v, (dict, list)):
                    nested[k] = v
                else:
                    primitives[k] = v

            st.markdown('<div class="saas-card" style="padding: 0.5rem 0;">', unsafe_allow_html=True)

            # Render key-value table for primitives
            for key, val in primitives.items():
                val_display = str(val) if val is not None else '<span style="color: #64748b;">null</span>'
                # Clickable URL detection
                if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://")):
                    val_display = f'<a href="{val}" target="_blank" style="color: #38bdf8; text-decoration: none;">{val} ↗</a>'

                st.markdown(f"""
                <div class="kv-row">
                    <div class="kv-key">{key}</div>
                    <div class="kv-val">{val_display}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # Render nested structures nicely
            if nested:
                st.markdown('<div style="font-size: 0.85rem; font-weight: 700; color: #94a3b8; margin: 1rem 0 0.5rem 0;">Nested Attributes & Collections</div>', unsafe_allow_html=True)
                for nest_key, nest_val in nested.items():
                    with st.expander(f"📦 {nest_key} ({len(nest_val) if hasattr(nest_val, '__len__') else 'Object'})", expanded=True):
                        st.json(nest_val)
        else:
            st.info("No data fields were parsed from the target URL.")

    with tab_json:
        st.json(cleaned_data if cleaned_data else {})

    # ==========================================================================
    # 7. REPORTS SECTION (CSV, JSON, PDF DOWNLOADS)
    # ==========================================================================
    st.markdown('<div class="section-heading" style="margin-top: 2rem;">📄 Intelligence Export & Reports</div>', unsafe_allow_html=True)

    csv_path = "output/extracted_data.csv"
    json_path = "output/extracted_data.json"
    pdf_path = "output/extracted_report.pdf"

    rep_col1, rep_col2, rep_col3 = st.columns(3)

    # CSV Card
    with rep_col1:
        st.markdown("""
        <div class="report-card">
            <div>
                <div class="report-icon">📊</div>
                <div class="report-title">Structured CSV</div>
                <div class="report-desc">Clean tabular dataset formatted for analysis in Pandas, Excel, or SQL databases.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if os.path.exists(csv_path):
            with open(csv_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name="extracted_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.button("CSV Unavailable", disabled=True, use_container_width=True)

    # JSON Card
    with rep_col2:
        st.markdown("""
        <div class="report-card">
            <div>
                <div class="report-icon">{ }</div>
                <div class="report-title">Clean JSON</div>
                <div class="report-desc">Full machine-readable hierarchy ready for REST API ingestion or NoSQL storage.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if os.path.exists(json_path):
            with open(json_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download JSON",
                    data=f,
                    file_name="extracted_data.json",
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.button("JSON Unavailable", disabled=True, use_container_width=True)

    # PDF Card
    with rep_col3:
        st.markdown("""
        <div class="report-card">
            <div>
                <div class="report-icon">📄</div>
                <div class="report-title">Executive PDF</div>
                <div class="report-desc">Formatted executive document report including summary, metrics, and data tables.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=f,
                    file_name="extracted_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.button("PDF Unavailable", disabled=True, use_container_width=True)


# ==============================================================================
# 9. PROFESSIONAL FOOTER
# ==============================================================================

st.markdown("""
<div class="saas-footer">
    <div>Intelligent Web Data Extraction Agent • v2.0 Enterprise Edition</div>
    <div style="margin-top: 0.35rem;">
        Powered by <span class="footer-tech">LangGraph</span> • 
        <span class="footer-tech">LangChain</span> • 
        <span class="footer-tech">Groq</span> • 
        <span class="footer-tech">Playwright</span>
    </div>
</div>
""", unsafe_allow_html=True)