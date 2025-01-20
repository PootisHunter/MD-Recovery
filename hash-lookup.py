import requests

api_key = "YOUR_API_KEY"
hash_value = "HASH_TO_LOOKUP"
url = f"https://www.virustotal.com/api/v3/files/{hash_value}"

headers = {"x-apikey": api_key}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(response.json())
else:
    print("Hash not found or API limit reached.")
