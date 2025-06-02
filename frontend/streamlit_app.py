# frontend/streamlit_app.py

import streamlit as st
import httpx
import asyncio
import nest_asyncio # Import nest_asyncio
from typing import List, Dict, Any, Optional

# Apply nest_asyncio to allow asyncio.run() within Streamlit's running loop
nest_asyncio.apply()

st.set_page_config(layout="wide")

# Assuming your FastAPI service runs on localhost:8000
API_BASE_URL = "http://127.0.0.1:8000"

# Use st.cache_resource to initialize the client once and reuse it
@st.cache_resource
def get_async_http_client():
    return httpx.AsyncClient(base_url=API_BASE_URL)

client = get_async_http_client()

st.title("🤝 AI Diplomacy Dojo & Peace Weaver 🕊️")
st.markdown("Practice your negotiation skills or get AI assistance for de-escalation.")

# --- Session Management ---
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
        st.session_state.negotiation_history = data["ai_responses"] # Initial AI greetings
        st.session_state.current_status = data["current_status"]
        st.session_state.agreed_points = data["agreed_points"]
        st.session_state.next_action_hint = data["next_action_hint"]
        st.success("Negotiation started!")
    except httpx.HTTPStatusError as e:
        st.error(f"Error starting negotiation: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        st.error(f"Network error: {e}. Is FastAPI server running?")

async def submit_user_turn_async(session_id: str, message: str):
    try:
        st.session_state.negotiation_history.append({"speaker_id": "user", "message": message})
        response = await client.post(
            "/negotiate/turn",
            json={
                "session_id": session_id,
                "speaker_id": "user",
                "message": message
            }
        )
        response.raise_for_status()
        data = response.json()
        for ai_res in data["ai_responses"]:
            st.session_state.negotiation_history.append(ai_res)
        st.session_state.current_status = data["current_status"]
        st.session_state.agreed_points = data["agreed_points"]
        st.session_state.next_action_hint = data["next_action_hint"]
    except httpx.HTTPStatusError as e:
        st.error(f"Error submitting turn: {e.response.status_code} - {e.response.text}")
        st.session_state.negotiation_history.pop() # Remove user message if error
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

async def facilitate_dialogue_async(speaker_id: str, message: str):
    try:
        response = await client.post(
            "/dialogue/facilitate",
            json={
                "session_id": "temp_session", # Placeholder for now
                "speaker_id": speaker_id,
                "message": message
            }
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
                if turn["speaker_id"] == "user":
                    st.markdown(f"**You:** {turn['message']}")
                else:
                    st.markdown(f"**{turn['speaker_id'].replace('_', ' ').title()}:** {turn['message']}")
            
        user_message = st.chat_input("Your next move in the negotiation:")
        if user_message and st.session_state.session_id:
            asyncio.run(submit_user_turn_async(st.session_state.session_id, user_message))
            st.rerun() # Rerun to update chat history

        if st.session_state.current_status != "ongoing" and st.session_state.session_id:
            if st.button("Get Negotiation Feedback"):
                asyncio.run(get_feedback_async(st.session_state.session_id))
    else:
        st.info("Start a new negotiation from the sidebar.")


with col2:
    st.header("Peace Weaver - Dialogue Facilitator (Prototype)")
    st.write("Type a message to analyze its sentiment and get de-escalation suggestions.")
    
    dialogue_speaker = st.text_input("Speaker ID (e.g., 'Party A', 'Party B')", "Anonymous")
    dialogue_message = st.text_area("Dialogue Segment to Analyze", height=100)
    
    if st.button("Analyze & Facilitate"):
        if dialogue_message:
            asyncio.run(facilitate_dialogue_async(dialogue_speaker, dialogue_message))
        else:
            st.warning("Please enter a message to analyze.")

st.markdown("---")
st.markdown("For Deep Funding AI for Peace Hackathon. Built for SingularityNET Marketplace.")