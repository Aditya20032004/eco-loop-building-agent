import requests
import time
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:14b"

class EcoLoopAgent:
    def __init__(self):
        self.model = MODEL_NAME
        
    def prompt_llm(self, prompt_text):
        """Sends a synchronous prompt to the local Ollama instance."""
        payload = {
            "model": self.model,
            "prompt": prompt_text,
            "stream": False,
            "temperature": 0.0  # Greedy decoding for deterministic control outputs
        }
        
        start_time = time.time()
        try:
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            latency = time.time() - start_time
            return data.get("response", "").strip(), latency
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Ollama: {e}")
            return "", 0.0

if __name__ == "__main__":
    print(f"Testing connection to local Ollama ({MODEL_NAME})...")
    agent = EcoLoopAgent()
    
    # Cold start test
    print("Sending cold-start prompt...")
    resp1, lat1 = agent.prompt_llm("Reply with exactly two words: 'System Online'.")
    print(f"Cold response: '{resp1}' (Latency: {lat1:.2f}s)")
    
    # Warm start test
    print("Sending warm-start prompt...")
    resp2, lat2 = agent.prompt_llm("What is 2+2? Reply with just the number.")
    print(f"Warm response: '{resp2}' (Latency: {lat2:.2f}s)")