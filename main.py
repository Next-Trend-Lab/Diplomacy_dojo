# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv # Import dotenv
load_dotenv() # Load environment variables from .env file

import asyncio
import uvicorn

# Import the updated services and models
from src.models.llm_agent import LLMAgent
from src.services.negotiation_service import NegotiationService
from src.services.audio_service import AudioService # NEW

# Pydantic models for request/response bodies (Modified for audio)
class AINegotiator(BaseModel):
    id: str
    persona_type: str
    initial_stance: str

class StartNegotiationRequest(BaseModel):
    scenario_id: str
    user_persona: str
    ai_negotiators: List[AINegotiator]

class AITurnResponse(BaseModel): # MODIFIED: Added audio_output_b64
    speaker_id: str
    message: str
    audio_output_b64: Optional[str] = None # Base64 encoded MP3 audio

class UserTurn(BaseModel): # MODIFIED: Added optional audio_input_b64
    session_id: str
    speaker_id: str
    message: Optional[str] = None # Text message (optional if audio is provided)
    audio_input_b64: Optional[str] = None # Base64 encoded audio from microphone

class NegotiationResponse(BaseModel):
    session_id: Optional[str] = None
    ai_responses: List[AITurnResponse]
    current_status: str
    agreed_points: List[str]
    next_action_hint: str

class DialogueFacilitateRequest(BaseModel): # MODIFIED: Added optional audio_input_b64
    session_id: str # Can be a placeholder like "temp_session" for facilitator
    speaker_id: str
    message: Optional[str] = None # Text message (optional if audio is provided)
    audio_input_b64: Optional[str] = None # Base64 encoded audio from microphone

class DialogueFacilitateResponse(BaseModel):
    sentiment_score: float
    escalation_flag: bool
    intervention: Optional[str]

# Initialize FastAPI app
app = FastAPI(
    title="AI Diplomacy Toolkit API (Google Cloud Edition)",
    description="Backend for AI Diplomacy simulations and dialogue facilitation.",
    version="1.0.0"
)

# Initialize services
# LLM agent (now uses Google Cloud Gemini)
llm_agent_instance = LLMAgent()
audio_service_instance = AudioService() # NEW: Instantiate AudioService
negotiation_service = NegotiationService(llm_agent_instance, audio_service_instance) # MODIFIED: Pass audio_service

# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": "AI Diplomacy Toolkit API is running. Visit /docs for API documentation."}

@app.get("/personas")
async def get_personas():
    """Returns a list of available AI persona types."""
    return {"personas": list(negotiation_service.persona_prompts.keys())}

@app.post("/negotiate/start", response_model=NegotiationResponse)
async def start_negotiation_endpoint(request: StartNegotiationRequest):
    """Starts a new negotiation session."""
    try:
        response_data = negotiation_service.start_negotiation(
            request.scenario_id,
            request.user_persona,
            [ai.dict() for ai in request.ai_negotiators]
        )
        return NegotiationResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start negotiation: {e}")

@app.post("/negotiate/turn", response_model=NegotiationResponse)
async def take_negotiation_turn_endpoint(request: UserTurn):
    """Submits a user's turn in an ongoing negotiation and gets AI responses."""
    if not request.message and not request.audio_input_b64:
        raise HTTPException(status_code=400, detail="Either 'message' or 'audio_input_b64' must be provided.")

    try:
        response_data = await negotiation_service.take_turn(
            request.session_id,
            request.speaker_id,
            message=request.message, # Pass text if provided
            audio_input_b64=request.audio_input_b64 # Pass audio if provided
        )
        return NegotiationResponse(**response_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process negotiation turn: {e}")

@app.get("/negotiate/{session_id}/feedback")
async def get_negotiation_feedback_endpoint(session_id: str):
    """Gets feedback for a completed negotiation session."""
    try:
        feedback = await negotiation_service.get_feedback(session_id)
        return feedback
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {e}")

@app.post("/dialogue/facilitate", response_model=DialogueFacilitateResponse)
async def facilitate_dialogue_endpoint(request: DialogueFacilitateRequest):
    """Analyzes a dialogue segment for sentiment and provides de-escalation suggestions."""
    if not request.message and not request.audio_input_b64:
        raise HTTPException(status_code=400, detail="Either 'message' or 'audio_input_b64' must be provided.")
        
    text_to_analyze = request.message

    if request.audio_input_b64:
        if not audio_service_instance: # Should not happen if initialized correctly
            raise HTTPException(status_code=500, detail="Audio service is not available.")
        try:
            # Run synchronous transcription in a separate thread
            text_to_analyze = await asyncio.to_thread(
                audio_service_instance.transcribe_audio, request.audio_input_b64
            )
        except Exception as e:
            # Handle transcription specific error
            raise HTTPException(status_code=500, detail=f"Audio transcription failed: {e}")

    if not text_to_analyze: # If audio was provided but transcription failed or returned empty, or no text message
        raise HTTPException(status_code=400, detail="Failed to get text from audio or no text message provided.")

    try:
        analysis = await negotiation_service.facilitate_dialogue(
            request.session_id,
            request.speaker_id,
            message=text_to_analyze
        )
        return DialogueFacilitateResponse(**analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to facilitate dialogue: {e}")

# If running directly (e.g., for local development)
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)