import requests
import json

url = "http://localhost:11434/v1/embeddings"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer NA"
}
data = {
    "model": "nomic-embed-text:latest",
    "input": "Test string for embedding"
}

try:
    print(f"Sending request to {url} with model {data['model']}...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if 'data' in result and len(result['data']) > 0 and 'embedding' in result['data'][0]:
            print("SUCCESS: Embedding received.")
            print(f"Embedding length: {len(result['data'][0]['embedding'])}")
        else:
            print("FAILURE: Response JSON does not contain expected 'data' -> 'embedding' structure.")
            print("Response:", json.dumps(result, indent=2))
    else:
        print("FAILURE: Request failed.")
        print("Response:", response.text)

except Exception as e:
    print(f"EXCEPTION: {e}")
