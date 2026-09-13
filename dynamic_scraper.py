from playwright.sync_api import sync_playwright

url = "https://example.com"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page()
    page.goto(url)

    print("TITLE:")
    print(page.title())

    print("\nURL:")
    print(page.url)

    print("\nPAGE TEXT:")
    print(page.locator("body").inner_text()[:2000])

    browser.close()