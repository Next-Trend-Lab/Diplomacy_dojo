# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.services.negotiation_manager import NegotiationManager
from src.models.personas import AI_NEGOTIATOR_PERSONAS
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

app = FastAPI(
    title="AI Diplomacy Dojo: Negotiation Simulator",
    description="An AI service for practicing negotiation skills against intelligent AI agents.",
    version="0.1.0"
)

# Initialize the negotiation manager (singleton pattern)
negotiation_manager = NegotiationManager()

# --- Pydantic Models for API Request/Response (matching .proto for eventual gRPC) ---

class NegotiatorDetails(BaseModel):
    id: str
    persona_type: str
    initial_stance: str

class StartNegotiationRequest(BaseModel):
    scenario_id: str
    user_persona: str
    ai_negotiators: List[NegotiatorDetails]

class NegotiationTurn(BaseModel):
    session_id: str
    speaker_id: str # "user" or AI ID
    message: str

class NegotiationResponse(BaseModel):
    session_id: str
    ai_responses: List[NegotiationTurn]
    current_status: str
    agreed_points: List[str]
    next_action_hint: str

class GetFeedbackResponse(BaseModel):
    session_id: str
    feedback_summary: str
    specific_suggestions: List[str]
    final_outcome: str

# --- API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Diplomacy Dojo! Use /docs for API documentation."}

@app.get("/personas")
async def get_available_personas():
    """Returns a list of available AI negotiator personas."""
    return {"personas": list(AI_NEGOTIATOR_PERSONAS.keys())}

@app.post("/negotiate/start", response_model=NegotiationResponse)
async def start_negotiation(request: StartNegotiationRequest):
    """
    Starts a new negotiation session.
    """
    # For a hackathon, define a few hardcoded scenarios or allow simple free-text.
    # Here, let's assume `scenario_id` corresponds to a simple description.
    # In a full app, you'd load from a data/scenarios.json
    
    # Example hardcoded scenario descriptions:
    scenario_descriptions = {
        "border_dispute_1": "Negotiation between two nations (Alpha and Beta) over a disputed border region with vital mineral resources.",
        "community_conflict_park": "A local community meeting to resolve conflict over the use of a shared public park, with differing views on commercial vs. recreational use."
    }
    scenario_desc = scenario_descriptions.get(request.scenario_id, "A general conflict resolution scenario.")


    try:
        response = await negotiation_manager.start_new_negotiation(
            scenario_id=request.scenario_id,
            scenario_description=scenario_desc,
            user_persona=request.user_persona,
            ai_negotiators_details=[n.dict() for n in request.ai_negotiators] # Convert Pydantic models to dicts
        )
        return NegotiationResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.post("/negotiate/turn", response_model=NegotiationResponse)
async def submit_user_turn(turn: NegotiationTurn):
    """
    Submits a user's turn in an ongoing negotiation session.
    """
    if turn.speaker_id != "user":
        raise HTTPException(status_code=400, detail="Only 'user' can submit a turn via this endpoint.")
    
    try:
        response = await negotiation_manager.submit_user_turn(turn.session_id, turn.message)
        return NegotiationResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/negotiate/{session_id}/feedback", response_model=GetFeedbackResponse)
async def get_negotiation_feedback(session_id: str):
    """
    Retrieves feedback for a completed negotiation session.
    """
    try:
        response = await negotiation_manager.get_negotiation_feedback(session_id)
        return GetFeedbackResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Agentic Dialogue Facilitator (Peace Weaver) - Initial Sketch ---

class DialogueSegment(BaseModel):
    session_id: str # For future persistent sessions
    speaker_id: str
    message: str

class FacilitatorResponse(BaseModel):
    session_id: str
    intervention: Optional[str] = None # The AI's suggested de-escalation message
    sentiment_score: float # E.g., from -1.0 to 1.0
    escalation_flag: bool # True if escalation detected

@app.post("/dialogue/facilitate", response_model=FacilitatorResponse)
async def facilitate_dialogue_segment(segment: DialogueSegment):
    """
    Analyzes a dialogue segment and provides de-escalation suggestions (Peace Weaver).
    For a hackathon, this might be a simpler, stateless endpoint.
    """
    # This part would integrate logic from the NegotiationManager or a new DialogueManager
    # For now, let's do a simple direct LLM call for a proof-of-concept.

    llm_agent = NegotiationManager().llm_agent # Reuse the LLM agent instance

    # Basic sentiment analysis (can be replaced with a dedicated model)
    sentiment_analysis_prompt = f"Analyze the sentiment of the following message and return a score between -1 (very negative) and 1 (very positive). Only return the score.\nMessage: \"{segment.message}\""
    sentiment_score_str = await llm_agent.generate_response(system_prompt="You are a sentiment analyzer.", user_message=sentiment_analysis_prompt, history=[])
    
    sentiment_score = 0.0
    try:
        sentiment_score = float(sentiment_score_str.strip())
    except ValueError:
        pass # Handle cases where LLM doesn't return a perfect float

    # Basic escalation detection (can be expanded)
    escalation_flag = sentiment_score < -0.5 # Simple heuristic

    intervention_message = None
    if escalation_flag:
        # Get intervention from LLM based on prompts.py
        intervention_prompt = get_deescalation_prompt(segment.message, full_conversation_history="") # For simplicity, no history
        intervention_message_raw = await llm_agent.generate_response(system_prompt="You are an AI Peace Weaver.", user_message=intervention_prompt, history=[])
        if "No intervention needed" not in intervention_message_raw:
            intervention_message = intervention_message_raw.strip()

    return FacilitatorResponse(
        session_id=segment.session_id, # Reusing session_id concept for potential future state
        intervention=intervention_message,
        sentiment_score=sentiment_score,
        escalation_flag=escalation_flag
    )