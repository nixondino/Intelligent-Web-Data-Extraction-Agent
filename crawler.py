import re
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError


class CrawlError(Exception):
    """Custom exception for structured crawler errors."""
    def __init__(self, error_type: str, message: str, status_code: int = None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return f"[{self.error_type}] {self.message}"


def normalize_url(url: str) -> str:
    """Normalize and validate target URL."""
    url = url.strip()
    if not url:
        raise CrawlError("INVALID_URL", "No URL provided. Please enter a valid website address.")

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    parsed = urllib.parse.urlparse(url)
    if not parsed.netloc or "." not in parsed.netloc:
        raise CrawlError("INVALID_URL", f"Invalid URL format: '{url}'. Please enter a valid domain name.")

    return url


def clean_dom_and_extract_text(html: str, url: str) -> str:
    """
    Cleans raw HTML aggressively to minimize Groq token consumption
    while preserving high-signal semantic content (articles, tables, specs).
    """
    soup = BeautifulSoup(html, "html.parser")

    # ==============================
    # 1. EXTRACT METADATA
    # ==============================
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.get_text(strip=True)
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()

    meta_description = ""
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
                    soup.find("meta", property=re.compile(r"og:description", re.I))
    if meta_desc_tag and meta_desc_tag.get("content"):
        meta_description = meta_desc_tag["content"].strip()

    author = ""
    author_tag = soup.find("meta", attrs={"name": re.compile(r"author", re.I)}) or \
                 soup.find("meta", property=re.compile(r"article:author", re.I))
    if author_tag and author_tag.get("content"):
        author = author_tag["content"].strip()

    date = ""
    date_tag = soup.find("meta", property=re.compile(r"article:published_time|og:updated_time", re.I)) or \
               soup.find("meta", attrs={"name": re.compile(r"date|pubdate", re.I)})
    if date_tag and date_tag.get("content"):
        date = date_tag["content"].strip()

    # ==============================
    # 2. REMOVE NOISY ELEMENTS
    # ==============================
    noisy_selectors = [
        "script", "style", "noscript", "svg", "iframe", "canvas",
        "nav", "footer", "header", "aside", "form", "dialog",
        ".cookie", ".cookie-banner", "#cookie-notice", ".cookie-consent",
        ".ad", ".advertisement", ".ad-container", ".social-share",
        ".sidebar", "#sidebar", ".newsletter-signup", ".popup", ".modal"
    ]
    for sel in noisy_selectors:
        for el in soup.select(sel):
            el.decompose()

    # ==============================
    # 3. FIND TARGET MAIN CONTAINER
    # ==============================
    main_container = None
    candidate_selectors = [
        "article",
        "main",
        '[role="main"]',
        ".article-body",
        ".article-content",
        ".post-content",
        ".entry-content",
        "#content",
        ".content",
        ".page-content",
        ".product-details",
        ".directory-listing"
    ]
    for sel in candidate_selectors:
        match = soup.select_one(sel)
        if match and len(match.get_text(strip=True)) > 200:
            main_container = match
            break

    target_root = main_container if main_container else (soup.body if soup.body else soup)

    # ==============================
    # 4. STRUCTURED TEXT EXTRACTION
    # ==============================
    lines = []
    for el in target_root.find_all(["h1", "h2", "h3", "h4", "p", "li", "tr", "dt", "dd"]):
        text = el.get_text(separator=" ", strip=True)
        if not text:
            continue
        if el.name in ["h1", "h2", "h3"]:
            lines.append(f"\n### {text}\n")
        elif el.name == "li":
            lines.append(f"- {text}")
        elif el.name == "tr":
            lines.append(f"| {text} |")
        else:
            lines.append(text)

    full_text = "\n".join(lines) if lines else target_root.get_text(separator=" ", strip=True)

    # Normalize excessive spaces and blank lines
    full_text = re.sub(r"[ \t]+", " ", full_text)
    full_text = re.sub(r"\n\s*\n+", "\n\n", full_text).strip()

    # Token optimization: Limit to ~8,000 characters of dense, high-signal text
    max_char_limit = 8000
    if len(full_text) > max_char_limit:
        full_text = full_text[:max_char_limit] + "\n... [Content truncated for token efficiency] ..."

    # ==============================
    # 5. ASSEMBLE CLEAN CONTENT
    # ==============================
    parts = [
        f"SOURCE URL: {url}",
        f"PAGE TITLE: {title}" if title else "PAGE TITLE: (Not specified)",
    ]
    if meta_description:
        parts.append(f"META DESCRIPTION: {meta_description}")
    if author:
        parts.append(f"AUTHOR: {author}")
    if date:
        parts.append(f"DATE: {date}")

    parts.append("\nMAIN CONTENT:")
    parts.append(full_text if full_text else "(No readable body text found)")

    return "\n".join(parts)


def crawl_website(raw_url: str) -> str:
    """
    Crawls website using Playwright with desktop emulation,
    robust error detection (DNS, 403, 404, timeouts), and returns
    token-optimized semantic content.
    """
    url = normalize_url(raw_url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )

            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                    timezone_id="America/New_York",
                    ignore_https_errors=True,
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
                    }
                )

                page = context.new_page()

                try:
                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=25000
                    )
                except PlaywrightTimeoutError:
                    raise CrawlError("TIMEOUT", f"Website took longer than 25 seconds to respond: {url}")
                except PlaywrightError as e:
                    err_str = str(e)
                    if "ERR_NAME_NOT_RESOLVED" in err_str or "getaddrinfo" in err_str:
                        raise CrawlError("DNS_FAILURE", f"Domain could not be resolved: {url}. Please verify the URL.")
                    elif "ERR_CONNECTION_REFUSED" in err_str:
                        raise CrawlError("CONNECTION_REFUSED", f"Target server refused connection: {url}")
                    elif "ERR_CONNECTION_TIMED_OUT" in err_str:
                        raise CrawlError("TIMEOUT", f"Connection timed out while reaching {url}")
                    else:
                        raise CrawlError("NETWORK_ERROR", f"Failed to load webpage: {err_str}")

                if response:
                    status = response.status
                    if status == 403:
                        raise CrawlError("HTTP_403", f"Access Denied (HTTP 403). The website blocked crawler access: {url}", status_code=403)
                    elif status == 404:
                        raise CrawlError("HTTP_404", f"Page Not Found (HTTP 404). The requested URL does not exist: {url}", status_code=404)
                    elif status >= 500:
                        raise CrawlError("SERVER_ERROR", f"Remote server error (HTTP {status}): {url}", status_code=status)

                # Wait briefly for dynamic JS rendering
                page.wait_for_timeout(800)
                html = page.content()
            finally:
                browser.close()

    except CrawlError:
        raise
    except Exception as e:
        raise CrawlError("CRAWLER_ERROR", f"Unexpected error during crawling: {str(e)}")

    clean_content = clean_dom_and_extract_text(html, url)

    # Content length verification
    if len(clean_content.strip()) < 80:
        raise CrawlError("EMPTY_CONTENT", f"The webpage at {url} returned empty or unparseable content.")

    return clean_content


if __name__ == "__main__":
    test_url = input("Enter website URL: ")
    try:
        content = crawl_website(test_url)
        print("\n--- EXTRACTED CONTENT ---")
        print(content[:1500])
        print(f"\nTotal characters: {len(content)}")
    except CrawlError as err:
        print(f"Crawler Error: {err}")