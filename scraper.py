import requests
from bs4 import BeautifulSoup

url = "https://example.com"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

# 1. Page title
print("TITLE:")
print(soup.title.text.strip())

# 2. Headings
print("\nHEADINGS:")
for heading in soup.find_all(["h1", "h2", "h3"]):
    print(heading.get_text(strip=True))

# 3. Paragraphs
print("\nPARAGRAPHS:")
for paragraph in soup.find_all("p"):
    print(paragraph.get_text(strip=True))

# 4. Links
print("\nLINKS:")
for link in soup.find_all("a"):
    text = link.get_text(strip=True)
    href = link.get("href")

    if text and href:
        print(text, "->", href)