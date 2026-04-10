import requests
import json

url = "http://127.0.0.1:8000/chat"
payload = {
    "message": "What is the notice period?",
    "history": [],
    "manual_lang": "English",
    "model": "Grok"
}

try:
    response = requests.post(url, json=payload, stream=True)
    full_text = ""
    print("Response from server:")
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode('utf-8'))
            if "delta" in chunk:
                full_text += chunk["delta"]
                print(chunk["delta"], end="", flush=True)
            elif "status" in chunk:
                print(f"\n[Status: {chunk['status']}]")
    print(f"\n\nFinal Full Response:\n{full_text}")
except Exception as e:
    print(f"Error: {e}")
