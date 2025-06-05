# frontend/streamlit_app.py

import streamlit as st
import httpx
import asyncio
from typing import List, Dict, Any, Optional
import base64 # Needed for encoding/decoding audio
from streamlit_mic_recorder import mic_recorder # NEW: For microphone input

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000" # Ensure this matches your FastAPI port
client = httpx.AsyncClient(base_url=API_BASE_URL)

# --- Streamlit Page Config (MUST be the first Streamlit command) ---
st.set_page_config(layout="wide", page_title="AI Diplomacy Toolkit (GC Edition)", page_icon="🤝")
st.title("🤝 AI Diplomacy Dojo & Peace Weaver 🕊️ (Google Cloud Edition)")
st.markdown("Practice your negotiation skills with voice or text, or get AI assistance for de-escalation.")

# --- Session State Initialization ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'negotiation_history' not in st.session_state:
    st.session_state.negotiation_history = []
if 'ai_personas_details' not in st.session_state:
    st.session_state.ai_personas_details = []
if 'current_status' not in st.session_state:
    st.session_state.current_status = "Not Started"
if 'agreed_points' not in st.session_state:
    st.session_state.agreed_points = []
if 'next_action_hint' not in st.session_state:
    st.session_state.next_action_hint = ""

# --- Backend API Calls (Async Functions) ---
async def get_personas():
    try:
        response = await client.get("/personas")
        response.raise_for_status()
        return response.json()["personas"]
    except httpx.HTTPStatusError as e:
        st.error(f"Error fetching personas: {e.response.status_code} - {e.response.text}")
        return []
    except httpx.RequestError as e:
        st.error(f"Network error connecting to backend: {e}. Is FastAPI server running at {API_BASE_URL}?")
        return []

async def start_negotiation_async(scenario_id: str, user_persona: str, ai_negotiators: List[Dict[str, str]]):
    try:
        response = await client.post(
            "/negotiate/start",
            json={
                "scenario_id": scenario_id,
                "user_persona": user_persona,
                "ai_negotiators": ai_negotiators
            }
        )
        response.raise_for_status()
        data = response.json()
        st.session_state.session_id = data["session_id"]
        # Initial AI responses might contain audio now
        st.session_state.negotiation_history = data["ai_responses"] 
        st.session_state.current_status = data["current_status"]
        st.session_state.agreed_points = data["agreed_points"]
        st.session_state.next_action_hint = data["next_action_hint"]
        st.success("Negotiation started!")
    except httpx.HTTPStatusError as e:
        st.error(f"Error starting negotiation: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        st.error(f"Network error: {e}. Is FastAPI server running?")

async def submit_user_turn_async(session_id: str, message: Optional[str] = None, audio_input_b64: Optional[str] = None): # MODIFIED
    try:
        # Add user's text message to history immediately for display
        if message:
            st.session_state.negotiation_history.append({"speaker_id": "user", "message": message})
        elif audio_input_b64:
             # Placeholder for transcribed text, will update if actual transcription available
             st.session_state.negotiation_history.append({"speaker_id": "user", "message": "*(Transcribing audio...)*"}) 

        response = await client.post(
            "/negotiate/turn",
            json={
                "session_id": session_id,
                "speaker_id": "user",
                "message": message, # Send text if available
                "audio_input_b64": audio_input_b64 # Send audio if available
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Update negotiation history with actual transcribed text (if audio was sent)
        # And add AI responses (with audio)
        st.session_state.negotiation_history = [
            {"speaker_id": h["speaker_id"], "message": h["message"], "audio_output_b64": h.get("audio_output_b64")}
            for h in data["ai_responses"] # Overwrite or merge based on history management
        ]
        # Re-add user's message after FastAPI confirms transcription
        if message:
             st.session_state.negotiation_history.insert(0, {"speaker_id": "user", "message": message})
        elif audio_input_b64 and data["ai_responses"]: # If audio was sent, first AI response might contain transcribed text
            # This is a simplified way; ideally, FastAPI returns the transcribed text directly
            # For now, we assume the first AI response implies the user's turn was processed.
            st.session_state.negotiation_history[0]["message"] = f"*(Audio input transcribed)*" # Update placeholder

        st.session_state.current_status = data["current_status"]
        st.session_state.agreed_points = data["agreed_points"]
        st.session_state.next_action_hint = data["next_action_hint"]
    except httpx.HTTPStatusError as e:
        st.error(f"Error submitting turn: {e.response.status_code} - {e.response.text}")
        if message: st.session_state.negotiation_history.pop() # Remove user message if error
    except httpx.RequestError as e:
        st.error(f"Network error: {e}. Is FastAPI server running?")

async def get_feedback_async(session_id: str):
    try:
        response = await client.get(f"/negotiate/{session_id}/feedback")
        response.raise_for_status()
        data = response.json()
        st.subheader("Negotiation Feedback")
        st.write(f"**Outcome:** {data['final_outcome']}")
        st.write(f"**Summary:** {data['feedback_summary']}")
        st.write("**Suggestions for Improvement:**")
        for suggestion in data['specific_suggestions']:
            st.write(f"- {suggestion}")
    except httpx.HTTPStatusError as e:
        st.error(f"Error getting feedback: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        st.error(f"Network error: {e}. Is FastAPI server running?")

async def facilitate_dialogue_async(speaker_id: str, message: Optional[str] = None, audio_input_b64: Optional[str] = None): # MODIFIED
    if not message and not audio_input_b64:
        st.warning("Please enter a message or record audio to analyze.")
        return

    try:
        payload = {
            "session_id": "temp_facilitator_session", # Placeholder
            "speaker_id": speaker_id,
            "message": message, # Send text if available
            "audio_input_b64": audio_input_b64 # Send audio if available
        }
        response = await client.post(
            "/dialogue/facilitate",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        st.info(f"**Sentiment Score:** {data['sentiment_score']:.2f} (Escalation: {data['escalation_flag']})")
        if data['intervention']:
            st.warning(f"**Peace Weaver Suggestion:** {data['intervention']}")
    except httpx.HTTPStatusError as e:
        st.error(f"Error facilitating dialogue: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        st.error(f"Network error: {e}. Is FastAPI server running?")


# --- UI Layout ---
st.sidebar.header("Configuration")
available_personas = asyncio.run(get_personas())

with st.sidebar.expander("Start New Negotiation", expanded=True):
    scenario_options = {
        "border_dispute_1": "Border Dispute (Country Alpha vs. Beta)",
        "community_conflict_park": "Community Park Usage Dispute",
        "general_conflict": "General Conflict Scenario"
    }
    selected_scenario_id = st.selectbox("Select Scenario", options=list(scenario_options.keys()), format_func=lambda x: scenario_options[x])
    user_persona_input = st.text_input("Your Role/Persona (e.g., 'Mediator', 'Country A Rep')", "User")

    num_ai_negotiators = st.slider("Number of AI Negotiators", 1, 3, 2)
    ai_negotiators_input = []
    for i in range(num_ai_negotiators):
        st.subheader(f"AI Negotiator {i+1}")
        ai_id = st.text_input(f"AI {i+1} ID", f"ai_{i+1}", key=f"ai_id_{i}")
        ai_persona_type = st.selectbox(f"AI {i+1} Persona Type", available_personas, key=f"ai_persona_type_{i}")
        ai_initial_stance = st.text_area(f"AI {i+1} Initial Stance", f"I represent the interests of side {ai_id}.", key=f"ai_stance_{i}")
        ai_negotiators_input.append({
            "id": ai_id,
            "persona_type": ai_persona_type,
            "initial_stance": ai_initial_stance
        })
    st.session_state.ai_personas_details = ai_negotiators_input # Store for feedback call

    if st.button("Start Negotiation"):
        st.session_state.negotiation_history = [] # Clear history on new session
        asyncio.run(start_negotiation_async(selected_scenario_id, user_persona_input, ai_negotiators_input))
        st.session_state.start_button_pressed = True


# --- Main Content Area ---
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Diplomacy Dojo - Negotiation Simulation")
    if st.session_state.session_id:
        st.write(f"**Session ID:** `{st.session_state.session_id}` | **Status:** `{st.session_state.current_status}`")
        if st.session_state.agreed_points:
            st.subheader("Agreed Points:")
            for point in st.session_state.agreed_points:
                st.markdown(f"- {point}")
        
        st.subheader("Conversation History")
        chat_placeholder = st.empty()
        
        with chat_placeholder.container():
            for turn in st.session_state.negotiation_history:
                speaker_name = turn["speaker_id"].replace('_', ' ').title()
                st.markdown(f"**{speaker_name}:** {turn['message']}")
                if turn.get("audio_output_b64"): # Play audio if available
                    # Streamlit expects base64 decoded bytes for st.audio
                    audio_bytes = base64.b64decode(turn["audio_output_b64"])
                    st.audio(audio_bytes, format='audio/mp3', sample_rate=44100) # Assuming MP3 from TTS


        # --- User Input Section (Text or Voice) ---
        st.subheader("Your Next Turn:")
        user_text_message = st.text_area("Type your message:", key="user_text_input", height=100)

        # Microphone recorder for audio input
        audio_recorder_data = mic_recorder(
            start_prompt="Start Recording",
            stop_prompt="Stop Recording",
            just_once=False, # Allows multiple recordings without rerun
            use_container_width=True,
            key='mic_recorder'
        )

        if st.button("Send Turn (Text)") and user_text_message and st.session_state.session_id:
            asyncio.run(submit_user_turn_async(st.session_state.session_id, message=user_text_message))
            st.session_state.user_text_input = "" # Clear text area
            st.rerun()
        elif audio_recorder_data and st.session_state.session_id:
            # audio_recorder_data will contain {'bytes': b'...', 'type': 'audio/webm'} or similar
            # Need to base64 encode the bytes to send to FastAPI
            audio_bytes = audio_recorder_data['bytes']
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            st.info("Sending audio for transcription and AI response...")
            asyncio.run(submit_user_turn_async(st.session_state.session_id, audio_input_b64=audio_b64))
            st.rerun() # Rerun to update chat history


        if st.session_state.current_status != "ongoing" and st.session_state.session_id:
            if st.button("Get Negotiation Feedback"):
                asyncio.run(get_feedback_async(st.session_state.session_id))
    else:
        st.info("Start a new negotiation from the sidebar.")


with col2:
    st.header("Peace Weaver - Dialogue Facilitator (Prototype)")
    st.write("Type a message or record audio to analyze its sentiment and get de-escalation suggestions.")
    
    dialogue_speaker = st.text_input("Speaker ID (e.g., 'Party A', 'Party B')", "Anonymous", key="facil_speaker_id")
    dialogue_message = st.text_area("Dialogue Segment to Analyze (Text)", height=100, key="facil_text_input")

    # Microphone for Facilitator
    facil_audio_recorder_data = mic_recorder(
        start_prompt="Start Recording (Facilitator)",
        stop_prompt="Stop Recording (Faciliator)",
        just_once=False,
        use_container_width=True,
        key='facil_mic_recorder'
    )
    
    if st.button("Analyze & Facilitate (Text)") and dialogue_message:
        asyncio.run(facilitate_dialogue_async(dialogue_speaker, message=dialogue_message))
        st.session_state.facil_text_input = "" # Clear text area
    elif facil_audio_recorder_data:
        audio_bytes = facil_audio_recorder_data['bytes']
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        st.info("Sending audio for analysis...")
        asyncio.run(facilitate_dialogue_async(dialogue_speaker, audio_input_b64=audio_b64))

st.markdown("---")
st.markdown("For Deep Funding AI for Peace Hackathon. Built for SingularityNET Marketplace.")