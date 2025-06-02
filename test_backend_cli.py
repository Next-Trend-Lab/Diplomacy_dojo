# test_backend_cli.py

import httpx
import asyncio
import json
import os

# Ensure this matches your FastAPI port
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

async def make_request(method: str, endpoint: str, json_data: dict = None, params: dict = None):
    """Helper function to make HTTP requests and handle responses."""
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        try:
            print(f"\n--- Requesting: {method.upper()} {API_BASE_URL}{endpoint} ---")
            if json_data:
                print(f"Payload: {json.dumps(json_data, indent=2)}")
            if params:
                print(f"Params: {params}")

            response = await client.request(method, endpoint, json=json_data, params=params)
            response.raise_for_status() # Raise an exception for 4xx/5xx responses
            print(f"Response Status: {response.status_code}")
            return response.json()
        except httpx.RequestError as e:
            print(f"Network error connecting to backend: {e}. Is FastAPI server running at {API_BASE_URL}?")
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

async def get_personas():
    """Fetches available AI personas from the backend."""
    print("\n--- Fetching Available Personas ---")
    data = await make_request("GET", "/personas")
    if data and "personas" in data:
        print(f"Available Personas: {data['personas']}")
        return data["personas"]
    return []

async def start_negotiation(scenario_id: str, user_persona: str, ai_negotiators: list):
    """Starts a new negotiation session."""
    print("\n--- Starting New Negotiation Session ---")
    payload = {
        "scenario_id": scenario_id,
        "user_persona": user_persona,
        "ai_negotiators": ai_negotiators
    }
    data = await make_request("POST", "/negotiate/start", json_data=payload)
    if data:
        session_id = data.get("session_id")
        ai_responses = data.get("ai_responses", [])
        print(f"Negotiation Session ID: {session_id}")
        print(f"Initial AI Responses: {json.dumps(ai_responses, indent=2)}")
        print(f"Current Status: {data.get('current_status')}")
        print(f"Next Action Hint: {data.get('next_action_hint')}")
        return session_id, ai_responses
    return None, []

async def submit_negotiation_turn(session_id: str, speaker_id: str, message: str):
    """Submits a turn in an ongoing negotiation."""
    print(f"\n--- Submitting Turn for Session: {session_id} ---")
    payload = {
        "session_id": session_id,
        "speaker_id": speaker_id,
        "message": message
    }
    data = await make_request("POST", "/negotiate/turn", json_data=payload)
    if data:
        print(f"Received AI Responses: {json.dumps(data.get('ai_responses'), indent=2)}")
        print(f"Updated Status: {data.get('current_status')}")
        print(f"Agreed Points: {data.get('agreed_points')}")
        print(f"Next Action Hint: {data.get('next_action_hint')}")
        return data.get('ai_responses', [])
    return []

async def get_negotiation_feedback(session_id: str):
    """Retrieves feedback for a completed negotiation."""
    print(f"\n--- Getting Feedback for Session: {session_id} ---")
    data = await make_request("GET", f"/negotiate/{session_id}/feedback")
    if data:
        print(f"Final Outcome: {data.get('final_outcome')}")
        print(f"Feedback Summary: {data.get('feedback_summary')}")
        print(f"Specific Suggestions: {json.dumps(data.get('specific_suggestions'), indent=2)}")

async def facilitate_dialogue(speaker_id: str, message: str):
    """Uses the Peace Weaver to analyze dialogue."""
    print(f"\n--- Facilitating Dialogue for Speaker: {speaker_id} ---")
    payload = {
        "session_id": "cli_dialogue_test", # A placeholder session ID for the facilitator
        "speaker_id": speaker_id,
        "message": message
    }
    data = await make_request("POST", "/dialogue/facilitate", json_data=payload)
    if data:
        print(f"Sentiment Score: {data.get('sentiment_score'):.2f}")
        print(f"Escalation Flag: {data.get('escalation_flag')}")
        print(f"Intervention Suggestion: {data.get('intervention')}")


async def main():
    # --- Example Usage ---

    print("--- Starting CLI Backend Test ---")

    # 1. (Optional) Get available personas first to confirm setup
    # await get_personas()

    # 2. Define AI Personas and Start a Negotiation
    scenario_id = "border_dispute_1"
    user_persona = "Country Alpha Representative"
    ai_negotiators = [
        {"id": "country_beta_ai", "persona_type": "hardliner", "initial_stance": "We stand firm on our historical claims to the entire disputed territory; it is non-negotiable as it is vital for our national security and economic prosperity. We expect full recognition of our sovereign rights."},
        {"id": "country_gamma_ai", "persona_type": "compromiser", "initial_stance": "Our primary objective is a peaceful and mutually beneficial resolution to this border issue. We are open to dialogue and exploring innovative solutions that ensure shared prosperity and stability for all parties involved, including potential resource sharing arrangements."},
        {"id": "country_delta_ai", "persona_type": "emotional_stakeholder", "initial_stance": "We represent the voices of the people living in the disputed zone, who have endured generations of uncertainty and hardship. Our priority is ensuring their safety, cultural heritage, and livelihood are unconditionally protected, and their suffering acknowledged by all parties."}
    ]

    session_id, initial_ai_responses = await start_negotiation(scenario_id, user_persona, ai_negotiators)

    if session_id:
        # Display initial AI greetings
        print("\n--- AI Greetings after Negotiation Start ---")
        for msg in initial_ai_responses:
            print(f"[{msg['speaker_id'].replace('_', ' ').title()}]: {msg['message']}")

        # 3. User makes a turn
        user_message_1 = "Greetings. We acknowledge the complexities of this situation and wish to open a dialogue towards a mutually agreeable border demarcation that respects all parties."
        ai_responses_turn1 = await submit_negotiation_turn(session_id, "user", user_message_1)
        print("\n--- AI Responses after User Turn 1 ---")
        for msg in ai_responses_turn1:
            print(f"[{msg['speaker_id'].replace('_', ' ').title()}]: {msg['message']}")

        # 4. Another User turn (example)
        user_message_2 = "While historical claims are certainly valid, the current inhabitants of the disputed zone deserve peace and stability. Could we consider a joint economic zone to benefit everyone, regardless of strict borders?"
        ai_responses_turn2 = await submit_negotiation_turn(session_id, "user", user_message_2)
        print("\n--- AI Responses after User Turn 2 ---")
        for msg in ai_responses_turn2:
            print(f"[{msg['speaker_id'].replace('_', ' ').title()}]: {msg['message']}")

        # You can continue adding more turns here to simulate a longer negotiation.
        # Example: A user turn leading to "agreed points" or "negotiation ended"
        # user_message_3 = "We propose an immediate ceasefire and a neutral observer mission to pave the way for formal talks."
        # await submit_negotiation_turn(session_id, "user", user_message_3)

        # 5. Get Feedback after turns
        await get_negotiation_feedback(session_id)
    else:
        print("Negotiation could not be started. Check FastAPI server.")

    # 6. Test the Dialogue Facilitator (Peace Weaver) independently
    print("\n--- Testing Peace Weaver (Dialogue Facilitator) ---")
    await facilitate_dialogue("Activist Group", "We demand immediate action! The current situation is an outrage!")
    await facilitate_dialogue("Community Leader", "Let's find common ground and work together to resolve this peacefully.")
    await facilitate_dialogue("Country Alpha Delegate", "Our position remains firm, but we are open to discussing the logistics of implementation.")


if __name__ == "__main__":
    asyncio.run(main())