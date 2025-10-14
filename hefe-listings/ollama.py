import json
import requests


OLLAMA_API_URL = "http://localhost:11434"


def api_is_up():
    try:
        response = requests.get(OLLAMA_API_URL)
        return response.status_code == 200
    except requests.ConnectionError:
        return False


# ollama models
def get_ollama_models():
    try:
        response = requests.get(f"{OLLAMA_API_URL}/api/tags")
        if response.status_code == 200:
            return response.json()["models"]
        else:
            print(f"Failed to get models: {response.status_code}")
            return []
    except requests.ConnectionError:
        print("Failed to connect to the API.")
        return []


# TODO: Use decorator for asserting API liveness? Or standard assertion??
def execute_ollama_model(model_name: str, prompt: str):
    try:
        payload = {
            "model": model_name,
            "prompt": prompt
        }
        print(f"Executing model {model_name} with prompt: {prompt}")
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate", json=payload)
        if response.status_code == 200:
            result = ""
            for line in response.iter_lines():
                if line:
                    data = line.decode('utf-8')
                    try:
                        json_obj = json.loads(data)
                        result += json_obj.get("response", "")
                    except Exception as e:
                        print(f"Failed to parse line: {e}")
            return {"text": result}
        else:
            print(f"Failed to execute model: {response.status_code}")
            return None
    except requests.ConnectionError:
        print("Failed to connect to the API.")
        return None
