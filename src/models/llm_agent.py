# src/models/llm_agent.py

from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part
from google.api_core.exceptions import GoogleAPIError
import os
from typing import List, Dict, Any, Optional
import vertexai

# --- Configuration for Google Cloud LLM ---
# Initialize Vertex AI for your project.
# GCP_PROJECT_ID must be set as an environment variable.
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
if not GCP_PROJECT_ID:
    raise ValueError(
        "The GCP_PROJECT_ID environment variable is not set. "
        "Please set it to your Google Cloud Project ID."
    )
# Default region 'us-central1' is generally fine.
vertexai.init(project=GCP_PROJECT_ID, location="us-central1")

class LLMAgent:
    def __init__(self, model_name: str = "gemini-1.5-pro-preview-0514", system_instruction: Optional[str] = None):
        """
        Initializes the LLM agent to use Google's Gemini model via Vertex AI.

        Args:
            model_name: The name of the Gemini model to use.
            system_instruction: Optional system-level instructions for the LLM.
                                This is passed directly to the GenerativeModel.
        """
        self.model_name = model_name
        self.model = GenerativeModel(
            self.model_name,
            system_instruction=Content(parts=[Part.from_text(system_instruction)]) if system_instruction else None
        )
        self.chat_session: Optional[ChatSession] = None

    def start_new_session(self, initial_messages: Optional[List[Dict[str, str]]] = None):
        """
        Starts a new chat session with the LLM.
        Initial messages can be provided to seed the conversation history.
        """
        history_contents: List[Content] = []
        if initial_messages:
            for msg in initial_messages:
                role = "user" if msg["role"] == "user" else "model" # Vertex AI uses 'user'/'model'
                history_contents.append(
                    Content(role=role, parts=[Part.from_text(msg["content"])])
                )
        
        self.chat_session = self.model.start_chat(history=history_contents if history_contents else None)

    def generate_response(self, user_message: str) -> str:
        """
        Generates a response from the LLM based on the user's message.
        """
        if self.chat_session is None:
            raise ValueError("Chat session has not been started. Call start_new_session() first.")

        try:
            response = self.chat_session.send_message(user_message)
            return response.text
        except GoogleAPIError as e:
            print(f"Google Cloud Vertex AI API error: {e}")
            # Consider more specific error handling or re-raising with context
            raise
        except Exception as e:
            print(f"Error generating response from LLM: {e}")
            raise