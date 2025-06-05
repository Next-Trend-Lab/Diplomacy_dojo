--- /dev/null
+++ b/C:/Users/Basrahtop/Desktop/AI Agents/ai_diplomacy_toolkit/README.md
@@ -0,0 +1,209 @@
+# AI Diplomacy Toolkit 交渉支援ツール
+
+[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
+[![Frameworks](https://img.shields.io/badge/Frameworks-FastAPI%20%7C%20Streamlit-green.svg)](https://fastapi.tiangolo.com/)
+[![Cloud Provider](https://img.shields.io/badge/Cloud-Google%20Cloud%20Platform-orange.svg)](https://cloud.google.com/)
+
+**Empowering effective communication and negotiation through advanced AI.**
+
+The AI Diplomacy Toolkit is a sophisticated platform designed to simulate complex negotiation scenarios and facilitate constructive dialogue. Leveraging the power of Google Cloud's Vertex AI (specifically Gemini models), Speech-to-Text, and Text-to-Speech services, this toolkit provides users with an interactive environment to practice, analyze, and enhance their diplomatic and communication skills.
+
+---
+
+## Table of Contents
+
+*   [🌟 Key Features](#-key-features)
+*   [🛠️ How It Works](#️-how-it-works)
+*   [⚙️ Tech Stack](#️-tech-stack)
+*   [🚀 Getting Started](#-getting-started)
+    *   [Prerequisites](#prerequisites)
+    *   [Setup Instructions](#setup-instructions)
+    *   [Running the Application](#running-the-application)
+*   [🔗 API Endpoints](#-api-endpoints)
+*   [🌐 Project Resources](#-project-resources)
+*   [🤝 Contributing](#-contributing)
+*   [📄 License](#-license)
+
+---
+
+## 🌟 Key Features
+
+*   **🤖 AI-Driven Negotiation Simulation:** Engage in realistic negotiation scenarios with AI agents powered by Google's Gemini models.
+*   **👥 Multi-AI Agent Interaction:** Configure and interact with multiple AI negotiators, each with distinct personas and stances.
+*   **🗣️ Voice-Enabled Interaction:** Communicate naturally using voice input (Speech-to-Text) and receive audio responses from AI agents (Text-to-Speech).
+*   **💬 Real-time Dialogue Facilitation:** Get AI-powered assistance to analyze dialogue, detect sentiment, flag potential escalations, and receive intervention suggestions.
+*   **📊 Negotiation Feedback:** Receive comprehensive feedback on completed negotiation sessions to identify areas for improvement.
+*   **🎭 Configurable AI Personas:** Define and customize AI agent personas and their initial stances to tailor simulation scenarios.
+*   **⚡ FastAPI Backend:** Robust and scalable backend API built with FastAPI.
+*   **🎨 Interactive Streamlit Frontend:** User-friendly interface built with Streamlit for easy interaction with the toolkit's features.
+
+---
+
+## 🛠️ How It Works
+
+The AI Diplomacy Toolkit operates with a decoupled frontend and backend architecture:
+
+1.  **Frontend (Streamlit):**
+    *   Provides the user interface for initiating negotiations, taking turns, facilitating dialogues, and viewing results.
+    *   Captures user input (text or audio) and sends requests to the FastAPI backend.
+    *   Displays responses and analysis received from the backend.
+
+2.  **Backend (FastAPI):**
+    *   **API Endpoints:** Exposes various RESTful endpoints for negotiation and dialogue facilitation.
+    *   **`NegotiationService`:** Orchestrates the core logic for negotiation simulations and dialogue analysis. It manages session state, interacts with AI agents, and processes user turns.
+    *   **`LLMAgent`:** Interfaces with Google Cloud Vertex AI to leverage Gemini models for generating AI responses, analyzing text, and providing feedback.
+    *   **`AudioService`:**
+        *   **Speech-to-Text:** Transcribes user's spoken input (if provided as audio) into text using Google Cloud Speech-to-Text.
+        *   **Text-to-Speech:** Converts AI-generated text responses into audible speech (MP3 format) using Google Cloud Text-to-Speech.
+    *   **Data Flow for a Negotiation Turn (with audio):**
+        *   User speaks into the microphone (captured by Streamlit frontend).
+        *   Frontend base64 encodes the audio and sends it to the `/negotiate/turn` endpoint.
+        *   FastAPI receives the request.
+        *   `AudioService` transcribes the audio to text.
+        *   `NegotiationService` processes the transcribed text, interacts with `LLMAgent` for AI responses.
+        *   `LLMAgent` (via Gemini) generates text responses for AI agents.
+        *   `AudioService` converts AI text responses to base64 encoded audio.
+        *   FastAPI returns text and audio responses to the Streamlit frontend.
+        *   Frontend displays text and allows playback of audio.
+
+3.  **Google Cloud Platform:**
+    *   **Vertex AI (Gemini):** Provides the core intelligence for AI agents' responses, dialogue analysis, and feedback generation.
+    *   **Cloud Speech-to-Text API:** Converts spoken audio into written text.
+    *   **Cloud Text-to-Speech API:** Synthesizes text into natural-sounding speech.
+
+---
+
+## ⚙️ Tech Stack
+
+*   **Backend:** Python 3.10+, FastAPI, Uvicorn
+*   **Frontend:** Python 3.10+, Streamlit
+*   **Cloud Services:** Google Cloud Platform
+    *   Vertex AI (Gemini Models)
+    *   Cloud Speech-to-Text API
+    *   Cloud Text-to-Speech API
+*   **Environment Management:** `python-dotenv`
+*   **Core AI Library:** `google-cloud-aiplatform`
+
+---
+
+## 🚀 Getting Started
+
+Follow these instructions to set up and run the AI Diplomacy Toolkit locally.
+
+### Prerequisites
+
+*   **Python:** Version 3.10 or higher.
+*   **Google Cloud SDK (`gcloud` CLI):** Installed and configured. Installation Guide.
+*   **Google Cloud Project:**
+    *   A Google Cloud Project with billing enabled.
+    *   The following APIs enabled in your project:
+        *   Vertex AI API
+        *   Cloud Speech-to-Text API
+        *   Cloud Text-to-Speech API
+*   **Git:** For cloning the repository.
+
+### Setup Instructions
+
+1.  **Clone the Repository:**
+    ```bash
+    git clone <your-repository-url>
+    cd ai_diplomacy_toolkit
+    ```
+
+2.  **Create and Activate a Virtual Environment:**
+    ```bash
+    python -m venv venv
+    # On Windows
+    .\venv\Scripts\activate
+    # On macOS/Linux
+    source venv/bin/activate
+    ```
+
+3.  **Install Dependencies:**
+    *(Ensure you have a `requirements.txt` file. If not, create one based on project imports.)*
+    ```bash
+    pip install -r requirements.txt
+    ```
+    *Likely dependencies for `requirements.txt` (create this file if it doesn't exist):*
+    ```
+    fastapi
+    uvicorn[standard]
+    pydantic
+    python-dotenv
+    google-cloud-aiplatform
+    google-cloud-speech
+    google-cloud-texttospeech
+    streamlit
+    requests
+    ```
+
+4.  **Configure Google Cloud:**
+    *   **Set Project ID:** Create a `.env` file in the project root (`ai_diplomacy_toolkit/.env`) and add your Google Cloud Project ID:
+        ```env
+        GCP_PROJECT_ID="your-actual-gcp-project-id-here"
+        ```
+        Replace `"your-actual-gcp-project-id-here"` with your actual Project ID.
+    *   **Authenticate with Google Cloud:** Run the following command in your terminal and follow the prompts to log in with your Google account that has access to the configured project and APIs:
+        ```bash
+        gcloud auth application-default login
+        ```
+        This sets up Application Default Credentials (ADC) which the Google Cloud client libraries will use.
+
+### Running the Application
+
+You'll need to run the backend and frontend in two separate terminal windows (with the virtual environment activated in both).
+
+1.  **Start the FastAPI Backend:**
+    In your first terminal, navigate to the project root and run:
+    ```bash
+    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
+    ```
+    You should see output indicating Uvicorn is running on `http://0.0.0.0:8000`.
+
+2.  **Start the Streamlit Frontend:**
+    In your second terminal, navigate to the project root and run:
+    ```bash
+    streamlit run streamlit_app.py
+    ```
+    Streamlit will typically open the application in your default web browser (usually at `http://localhost:8501`).
+
+---
+
+## 🔗 API Endpoints
+
+The FastAPI backend provides several endpoints. For detailed information, interactive testing, and request/response schemas, visit the auto-generated API documentation once the backend is running:
+
+*   **Swagger UI:** `http://127.0.0.1:8000/docs`
+*   **ReDoc:** `http://127.0.0.1:8000/redoc`
+
+Key endpoints include:
+*   `GET /`: Root health check.
+*   `GET /personas`: List available AI negotiator personas.
+*   `POST /negotiate/start`: Initiate a new negotiation session.
+*   `POST /negotiate/turn`: Submit a user's turn in an ongoing negotiation.
+*   `GET /negotiate/{session_id}/feedback`: Retrieve feedback for a session.
+*   `POST /dialogue/facilitate`: Analyze a dialogue segment for facilitation.
+
+---
+
+## 🌐 Project Resources
+
+*   **Landing Page:** `(To Be Added)`
+*   **Pitch Deck:** `(To Be Added)`
+*   **Video Presentation/Demo:** `(To Be Added)`
+
+---
+
+## 🤝 Contributing
+
+Contributions are welcome! If you'd like to contribute, please follow these steps:
+1.  Fork the repository.
+2.  Create a new branch (`git checkout -b feature/your-feature-name`).
+3.  Make your changes.
+4.  Commit your changes (`git commit -m 'Add some feature'`).
+5.  Push to the branch (`git push origin feature/your-feature-name`).
+6.  Open a Pull Request.
+
+Please ensure your code adheres to good practices and includes relevant tests if applicable.
+
+---
+
+## 📄 License
+
+This project is licensed under the `Apache 2.0` - see the `LICENSE` file for details (To Be Added).
+
+---
+
+Happy Negotiating!
+
+```
