# src/services/negotiation_manager.py

import uuid
from typing import Dict, List, Any
from collections import defaultdict
from src.models.llm_agent import LLMAgent
from src.utils.prompts import get_system_prompt_for_negotiator, get_feedback_prompt

class NegotiationManager:
    _instance = None
    _sessions: Dict[str, Dict[str, Any]] = {} # Store active sessions

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NegotiationManager, cls).__new__(cls)
            cls._instance._sessions = {} # Initialize sessions when first instance is created
        return cls._instance

    def __init__(self):
        # This init will run every time __new__ returns an instance, but we only need to init _sessions once.
        # So, we check if it's already initialized.
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # LLM agents can be shared if they use the same model, or create new ones per session if needed.
            # For simplicity, let's have one central LLM agent for now.
            self.llm_agent = LLMAgent()

    async def start_new_negotiation(self, scenario_id: str, scenario_description: str,
                                     user_persona: str, ai_negotiators_details: List[Dict[str, str]]) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        
        session_history = [] # Full chronological history of messages
        
        # Initialize AI agents with their specific history for turn-based interactions
        ai_agents_state = {}
        for ai_detail in ai_negotiators_details:
            ai_agents_state[ai_detail["id"]] = {
                "persona_type": ai_detail["persona_type"],
                "initial_stance": ai_detail["initial_stance"],
                "history": [], # Individual history for each AI agent to maintain its context
            }
        
        self._sessions[session_id] = {
            "scenario_id": scenario_id,
            "scenario_description": scenario_description,
            "user_persona": user_persona,
            "ai_negotiators_details": ai_negotiators_details,
            "ai_agents_state": ai_agents_state,
            "full_transcript": [], # Raw messages from all parties, for feedback
            "agreed_points": [],
            "status": "ongoing"
        }
        
        # Initial greeting from AI agents
        initial_ai_responses = []
        for ai_id, ai_state in ai_agents_state.items():
            system_prompt = get_system_prompt_for_negotiator(
                ai_state["persona_type"], ai_state["initial_stance"], scenario_description
            )
            # Send an initial "hello" or opening statement from each AI
            initial_message = "Hello, I'm ready to begin the negotiation." # Can be made smarter later
            ai_response = await self.llm_agent.generate_response(system_prompt, initial_message, [])
            ai_state["history"].append({"role": "user", "content": initial_message}) # The AI's internal history records what it was prompted with
            ai_state["history"].append({"role": "assistant", "content": ai_response})
            
            session_history.append({"speaker_id": ai_id, "message": ai_response})
            initial_ai_responses.append({"speaker_id": ai_id, "message": ai_response})

        self._sessions[session_id]["full_transcript"] = session_history
        
        return {
            "session_id": session_id,
            "ai_responses": initial_ai_responses,
            "current_status": self._sessions[session_id]["status"],
            "agreed_points": self._sessions[session_id]["agreed_points"],
            "next_action_hint": "It's your turn. Make an opening statement."
        }

    async def submit_user_turn(self, session_id: str, user_message: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            raise ValueError("Session not found.")
        
        session = self._sessions[session_id]
        scenario_description = session["scenario_description"]

        # Add user's message to the full transcript
        session["full_transcript"].append({"speaker_id": "user", "message": user_message})

        ai_responses = []
        for ai_id, ai_state in session["ai_agents_state"].items():
            system_prompt = get_system_prompt_for_negotiator(
                ai_state["persona_type"], ai_state["initial_stance"], scenario_description,
                session_history="\n".join([f"{t['speaker_id']}: {t['message']}" for t in session["full_transcript"]])
            )
            
            # The AI's internal history is updated to include the user's latest message
            # and then its own response
            ai_state["history"].append({"role": "user", "content": user_message})
            
            # Generate AI's response
            ai_response_content = await self.llm_agent.generate_response(
                system_prompt, user_message, ai_state["history"] # Pass the AI's individual history
            )
            
            ai_state["history"].append({"role": "assistant", "content": ai_response_content})
            session["full_transcript"].append({"speaker_id": ai_id, "message": ai_response_content})
            
            ai_responses.append({"speaker_id": ai_id, "message": ai_response_content})
        
        # Placeholder for updating status and agreed points (more complex logic needed)
        # You'd parse AI responses for keywords, or use another LLM call to detect agreements.
        # For hackathon, keep this simple or manual.
        # if "I agree" in user_message.lower():
        #     session["agreed_points"].append("User agreed to X")
        
        # Simple rule for status: if "I concede" from user or AI, then maybe "agreement reached"
        # Or based on number of turns.
        if len(session["full_transcript"]) > 20 and session["status"] == "ongoing": # Arbitrary turn limit
             session["status"] = "concluded_without_agreement"
             # Or more sophisticated logic to check for agreement keywords in the transcript.
        
        return {
            "session_id": session_id,
            "ai_responses": ai_responses,
            "current_status": session["status"],
            "agreed_points": session["agreed_points"],
            "next_action_hint": "Consider your next move. What's your proposal?"
        }

    async def get_negotiation_feedback(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            raise ValueError("Session not found.")
        
        session = self._sessions[session_id]
        full_transcript_str = "\n".join([f"{t['speaker_id']}: {t['message']}" for t in session["full_transcript"]])
        
        feedback_prompt = get_feedback_prompt(
            negotiation_transcript=full_transcript_str,
            user_persona=session["user_persona"],
            ai_personas=session["ai_negotiators_details"]
        )
        
        feedback_raw = await self.llm_agent.generate_response(system_prompt="You are a negotiation coach providing concise and actionable feedback.", user_message=feedback_prompt, history=[])
        
        # Parse feedback_raw into structured format. For hackathon, a single string is fine.
        # In a real app, you might use regex or another LLM call to extract points.
        
        return {
            "session_id": session_id,
            "feedback_summary": feedback_raw,
            "specific_suggestions": ["(Detailed suggestions can be parsed here)", "Focus on active listening"],
            "final_outcome": session["status"] # Assuming status is set during turns or determined here
        }