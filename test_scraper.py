import requests

url = "https://example.com"

response = requests.get(url)

print("Status Code:", response.status_code)
print(response.text[:1000])