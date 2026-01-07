
import requests
import json

def test_manual():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen3-coder:latest",
        "prompt": "Hi",
        "stream": False
    }
    print(f"Testing POST to {url} with model qwen3-coder:latest")
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_manual()
