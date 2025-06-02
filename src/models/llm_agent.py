# src/models/llm_agent.py

import httpx
import json
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class LLMAgent:
    def __init__(self, model_name: str = "llama3"):
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name
        self.client = httpx.AsyncClient(base_url=self.ollama_base_url, timeout=300.0) # Increased timeout

    async def generate_response(self, system_prompt: str, user_message: str, history: List[Dict[str, str]]) -> str:
        """Generates a response from the LLM based on system prompt, user message, and history."""
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]

        try:
            response = await self.client.post(
                "/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False # Set to False for direct response
                }
            )
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()
            return data["message"]["content"]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return f"Error: Failed to get response from LLM. HTTP Status: {e.response.status_code}"
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
            return f"Error: Failed to connect to LLM. Please ensure Ollama is running at {self.ollama_base_url}"
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return f"Error: An unexpected error occurred with the LLM call: {e}"