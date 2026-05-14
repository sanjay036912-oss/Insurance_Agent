import requests
import json

def extract_with_local_llm(text, existing_data):
    prompt = f"""
Extract insurance claim fields as JSON.

Existing data:
{json.dumps(existing_data)}

Text:
{text[:3000]}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )

        output = response.json()["response"]
        return json.loads(output)

    except:
        return existing_data