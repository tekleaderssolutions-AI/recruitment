import requests
import time

print("Testing HR dashboard endpoint...")
try:
    response = requests.get("http://localhost:8000/interviews/status", timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")
    if response.status_code != 200:
        print(f"Error: {response.text[:500]}")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 5 seconds")
except Exception as e:
    print(f"ERROR: {e}")
