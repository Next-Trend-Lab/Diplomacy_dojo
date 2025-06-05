# src/services/negotiation_service.py

from typing import List, Dict, Any, Optional
import json
import uuid

# Import the updated LLMAgent and the new AudioService
from src.models.llm_agent import LLMAgent
from src.services.audio_service import AudioService # NEW

class NegotiationService:
    def __init__(self, llm_agent: LLMAgent, audio_service: AudioService): # MODIFIED
        self.llm_agent = llm_agent
        self.audio_service = audio_service # NEW: Inject AudioService
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.persona_prompts = {
            "hardliner": "You are a hardline negotiator. Your goal is to cede no ground and maximize your nation's gains, even at the risk of escalating tensions. Stick firmly to your initial stance and historical claims. Do not compromise easily.",
            "compromiser": "You are a pragmatic compromiser. Your goal is to find common ground and achieve a mutually beneficial resolution, avoiding escalation. Be open to flexible solutions and resource sharing.",
            "emotional_stakeholder": "You represent the deeply affected populace. Your goal is to ensure the safety, cultural heritage, and livelihoods of the people in the disputed zone are protected. Emphasize human suffering and the need for justice, appealing to empathy."
        }

    def start_negotiation(self, scenario_id: str, user_persona: str, ai_negotiators: List[Dict[str, str]]):
        session_id = str(uuid.uuid4())
        
        # Initialize LLM for each AI persona
        ai_llm_configs = {}
        initial_ai_responses = []

        # Prepare system instructions for each AI agent
        system_instructions_map = {}
        for ai_info in ai_negotiators:
            persona_type = ai_info["persona_type"]
            initial_stance = ai_info["initial_stance"]
            base_prompt = self.persona_prompts.get(persona_type, "You are a negotiator.")
            full_prompt = f"{base_prompt} Your initial stance: '{initial_stance}'."
            system_instructions_map[ai_info["id"]] = full_prompt

        # Start LLM sessions for each AI and get initial greetings
        for ai_info in ai_negotiators:
            ai_id = ai_info["id"]
            # A new LLMAgent instance for each AI, passing system instructions at initialization
            ai_llm_instance = LLMAgent(system_instruction=system_instructions_map[ai_id])
            
            # Start session with initial context (system instructions will be part of the first prompt)
            # System instructions are now handled by the model itself.
            ai_llm_instance.start_new_session() 
            ai_llm_configs[ai_id] = ai_llm_instance

            # Generate initial greeting from AI based on its stance
            greeting_prompt = f"As the {ai_info['persona_type']} representing {ai_id}, provide a brief opening statement to the user representing {user_persona} about this negotiation."
            try:
                greeting_message = ai_llm_instance.generate_response(greeting_prompt)
                initial_ai_responses.append({
                    "speaker_id": ai_id,
                    "message": greeting_message
                })
            except Exception as e:
                print(f"Error generating initial greeting for {ai_id}: {e}")
                initial_ai_responses.append({
                    "speaker_id": ai_id,
                    "message": f"Error: Could not generate initial greeting. ({e})"
                })


        self.sessions[session_id] = {
            "scenario_id": scenario_id,
            "user_persona": user_persona,
            "ai_negotiators": ai_negotiators,
            "ai_llm_configs": ai_llm_configs, # Store LLM instances
            "conversation_history": [], # Store all text turns
            "current_status": "ongoing",
            "agreed_points": [],
            "next_action_hint": "Please make your opening statement."
        }
        
        # Add initial AI responses to history
        self.sessions[session_id]["conversation_history"].extend(initial_ai_responses)

        return {
            "session_id": session_id,
            "ai_responses": initial_ai_responses,
            "current_status": self.sessions[session_id]["current_status"],
            "agreed_points": self.sessions[session_id]["agreed_points"],
            "next_action_hint": self.sessions[session_id]["next_action_hint"]
        }

    async def take_turn(self, session_id: str, speaker_id: str, message: Optional[str] = None, audio_input_b64: Optional[str] = None): # MODIFIED
        if session_id not in self.sessions:
            raise ValueError("Session not found.")

        session = self.sessions[session_id]
        
        # --- Handle User Input (Text or Audio) ---
        user_text_message = message
        if audio_input_b64:
            try:
                user_text_message = self.audio_service.transcribe_audio(audio_input_b64)
                print(f"Transcribed user audio to: {user_text_message}")
            except Exception as e:
                return {"ai_responses": [], "current_status": "error", "agreed_points": [], "next_action_hint": f"Audio transcription failed: {e}"}

        if not user_text_message:
            return {"ai_responses": [], "current_status": session["current_status"], "agreed_points": session["agreed_points"], "next_action_hint": "No valid input provided."}


        # Record user's turn in history
        session["conversation_history"].append({"speaker_id": speaker_id, "message": user_text_message})

        ai_responses_data = []
        
        # Craft prompt for AI agents
        # Include a summary of history for context, or pass full history
        conversation_context = "\n".join([f"{t['speaker_id'].replace('_', ' ').title()}: {t['message']}" for t in session["conversation_history"][-5:]]) # Last 5 turns for context
        
        for ai_info in session["ai_negotiators"]:
            ai_id = ai_info["id"]
            ai_llm_instance = session["ai_llm_configs"][ai_id]
            
            # Combine system instructions, context, and user message for the AI's turn
            turn_prompt = f"Given the conversation context below, and your role as {ai_info['persona_type']} (initial stance: '{ai_info['initial_stance']}'), respond to the user's latest statement: '{user_text_message}'\n\nConversation Context (recent):\n{conversation_context}\n\nYour response:"
            
            try:
                ai_response_text = ai_llm_instance.generate_response(turn_prompt)
                
                # --- Synthesize AI response to audio ---
                ai_audio_b64 = self.audio_service.synthesize_speech(ai_response_text) # NEW
                
                ai_responses_data.append({
                    "speaker_id": ai_id,
                    "message": ai_response_text,
                    "audio_output_b64": ai_audio_b64 # NEW
                })
                # Record AI's turn in history
                session["conversation_history"].append({"speaker_id": ai_id, "message": ai_response_text})

            except Exception as e:
                print(f"Error generating AI response for {ai_id}: {e}")
                ai_responses_data.append({
                    "speaker_id": ai_id,
                    "message": f"Error: Could not generate response. ({e})",
                    "audio_output_b64": None
                })


        # Simple logic for agreement/status update (can be expanded with LLM analysis)
        if "agreement" in user_text_message.lower() or "deal" in user_text_message.lower():
            session["current_status"] = "agreement_proposed"
            session["next_action_hint"] = "Consider formalizing an agreement."
            session["agreed_points"].append("User proposed an agreement.")
        elif "end negotiation" in user_text_message.lower():
            session["current_status"] = "ended"
            session["next_action_hint"] = "Negotiation concluded."

        return {
            "ai_responses": ai_responses_data,
            "current_status": session["current_status"],
            "agreed_points": session["agreed_points"],
            "next_action_hint": session["next_action_hint"]
        }

    async def get_feedback(self, session_id: str):
        if session_id not in self.sessions:
            raise ValueError("Session not found.")
        
        session = self.sessions[session_id]
        
        # Use LLM to analyze conversation and provide feedback
        feedback_prompt = (
            "Analyze the following negotiation conversation and provide feedback on the user's performance. "
            "Identify key moments, effective strategies used, areas for improvement, and suggest alternative approaches. "
            "Also, provide a final outcome based on the conversation status (e.g., 'Agreement Reached', 'Stalemate', 'Escalated').\n\n"
            "Conversation History:\n" + 
            "\n".join([f"{t['speaker_id'].replace('_', ' ').title()}: {t['message']}" for t in session["conversation_history"]]) +
            f"\n\nUser's Initial Persona: {session['user_persona']}"
        )
        
        # Create a temporary LLM for feedback (doesn't need to be part of the session's AI configs)
        feedback_llm = LLMAgent()
        feedback_llm.start_new_session() 
        
        try:
            feedback_response_json_str = feedback_llm.generate_response(feedback_prompt + "\n\nProvide feedback in a JSON format with keys: 'final_outcome', 'feedback_summary', 'specific_suggestions' (as a list of strings).")
            # Attempt to parse as JSON. If not JSON, return raw text.
            try:
                feedback_data = json.loads(feedback_response_json_str)
            except json.JSONDecodeError:
                print(f"Warning: Feedback not in JSON format. Raw response: {feedback_response_json_str}")
                feedback_data = {
                    "final_outcome": session["current_status"],
                    "feedback_summary": "Could not parse detailed feedback. Raw LLM response: " + feedback_response_json_str,
                    "specific_suggestions": []
                }
            
            return feedback_data
        except Exception as e:
            print(f"Error generating feedback: {e}")
            return {
                "final_outcome": session["current_status"],
                "feedback_summary": f"Error generating detailed feedback: {e}",
                "specific_suggestions": ["Ensure LLM service is running and accessible."]
            }

    async def facilitate_dialogue(self, session_id: str, speaker_id: str, message: str): # MODIFIED: Add session_id for context if desired
        """Analyzes a dialogue segment and provides de-escalation suggestions."""
        # For simple facilitator, session_id might just be a placeholder.
        # For more complex, it could use past dialogue history.
        
        analysis_prompt = (
            f"Analyze the following statement from '{speaker_id}' in a dialogue context: '{message}'. "
            "Determine its sentiment (e.g., 'positive', 'neutral', 'negative'). "
            "Assign an escalation flag (True if highly escalatory, False otherwise). "
            "If escalatory or negative, provide a single, short de-escalation or constructive intervention suggestion. "
            "Provide the output in JSON format with keys: 'sentiment_score' (float between -1.0 to 1.0), 'escalation_flag' (boolean), 'intervention' (string, or null if no intervention needed)."
        )

        facilitator_llm = LLMAgent()
        facilitator_llm.start_new_session() 

        try:
            raw_response = facilitator_llm.generate_response(analysis_prompt)
            # Attempt to parse as JSON. If not JSON, try to extract parts or return default.
            try:
                analysis = json.loads(raw_response)
            except json.JSONDecodeError:
                print(f"Warning: Facilitator output not in JSON format. Raw: {raw_response}")
                # Fallback to basic parsing if JSON fails
                sentiment_match = "neutral"
                if "positive" in raw_response.lower(): sentiment_match = "positive"
                elif "negative" in raw_response.lower(): sentiment_match = "negative"

                escalation_flag = "true" in raw_response.lower() and "escalation flag: true" in raw_response.lower()

                intervention_text = "N/A"
                if "intervention:" in raw_response.lower():
                    intervention_text = raw_response.split("intervention:")[-1].strip().split("\n")[0] # Basic extraction

                analysis = {
                    "sentiment_score": 0.0, # Cannot determine precisely without JSON
                    "escalation_flag": escalation_flag,
                    "intervention": intervention_text
                }
                if sentiment_match == "positive": analysis["sentiment_score"] = 0.8
                elif sentiment_match == "negative": analysis["sentiment_score"] = -0.8
                
            return analysis
        except Exception as e:
            print(f"Error in dialogue facilitation: {e}")
            return {
                "sentiment_score": 0.0,
                "escalation_flag": True, # Default to true on error for safety
                "intervention": f"Error processing dialogue: {e}. Check LLM service."
            }