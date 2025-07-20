import requests
r = requests.get("https://api.ocr.space")
print(r.status_code)
