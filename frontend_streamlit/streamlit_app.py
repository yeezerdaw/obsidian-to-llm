import streamlit as st
import requests
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# --- Configuration for API ---
API_BASE_URL = "http://localhost:8000"

# --- Helper Functions to Call API (Same as before) ---
def handle_api_response(response: requests.Response):
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            st.error(f"Error decoding JSON response: {response.text}")
            return None
    elif response.status_code == 204:
        return {"message": "Operation successful (No content returned)."}
    else:
        try:
            error_data = response.json()
            detail = error_data.get("detail", "Unknown error")
            st.error(f"API Error (Status {response.status_code}): {detail}")
        except json.JSONDecodeError:
            st.error(f"API Error (Status {response.status_code}): {response.text}")
        return None

def call_api(method: str, endpoint: str, params: Optional[dict] = None, json_payload: Optional[dict] = None):
    """Generic API call helper."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, params=params, json=json_payload)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        return handle_api_response(response)
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to API at {API_BASE_URL}. Is the FastAPI server running?")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="ObsidianGPT", layout="centered", initial_sidebar_state="expanded")

# --- Custom CSS (Minimal for now) ---
# For more advanced styling, you'd save this to a .css file and load it.
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem; /* Add some space at the top */
    }
    .stTextInput > div > div > input { /* Style text input */
        border: 1px solid #4A4A4A;
    }
    .stTextArea > div > div > textarea {
        border: 1px solid #4A4A4A;
    }
    /* Attempt to mimic chat bubbles */
    .user-query {
        background-color: #2b313e; /* Darker blue/grey for user */
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: right;
    }
    .gpt-response {
        background-color: #40414f; /* ChatGPT-like dark grey for AI */
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)


# --- Session State ---
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = "Welcome"
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'note_context' not in st.session_state: # For storing context like selected note
    st.session_state.note_context = {}


# --- Sidebar for Mode Selection ---
with st.sidebar:
    st.title("ObsidianGPT ✨")
    st.caption("Your AI Second Brain Assistant")
    st.markdown("---")
    
    mode_options = {
        "Welcome": "👋 Welcome",
        "Find Notes": "🔍 Find Notes",
        "Query Note": "❓ Query a Note",
        "Process Note": "⚙️ Process a Note",
        "Analyze Connections": "🔗 Analyze Connections",
        "Daily Note Toolkit": "📅 Daily Note Toolkit"
    }
    
    def set_mode(mode_key):
        st.session_state.current_mode = mode_key
        st.session_state.last_query = "" # Reset query/response when changing mode
        st.session_state.last_response = None

    for key, value in mode_options.items():
        if st.button(value, key=f"mode_btn_{key}", on_click=set_mode, args=(key,), use_container_width=True):
            pass # on_click handles the mode change

    st.markdown("---")
    st.info(f"API: `{API_BASE_URL}`")


# --- Main Chat-like Interface ---
st.header(f"ObsidianGPT: {mode_options.get(st.session_state.current_mode, 'Interaction Mode')}")

# Placeholder for conversation history (simplified)
chat_container = st.container() # Use a container to manage chat display

with chat_container:
    if st.session_state.last_query:
        st.markdown(f"<div class='user-query'>🧑‍💻 You: {st.session_state.last_query}</div>", unsafe_allow_html=True)
    if st.session_state.last_response:
        if isinstance(st.session_state.last_response, str):
            st.markdown(f"<div class='gpt-response'>🤖 ObsidianGPT: {st.session_state.last_response}</div>", unsafe_allow_html=True)
        elif isinstance(st.session_state.last_response, dict) or isinstance(st.session_state.last_response, list):
             st.markdown("<div class='gpt-response'>🤖 ObsidianGPT:</div>", unsafe_allow_html=True)
             st.json(st.session_state.last_response, expanded=True) # Show JSON nicely
        else:
            st.markdown(f"<div class='gpt-response'>🤖 ObsidianGPT: {str(st.session_state.last_response)}</div>", unsafe_allow_html=True)


# --- Input Area at the bottom (conceptually) or specific to mode ---

if st.session_state.current_mode == "Welcome":
    st.markdown("Hello! I'm ObsidianGPT, your AI assistant for your Obsidian vault. Select an action from the sidebar to get started.")
    st.markdown("""
    **What I can do:**
    - **Find Notes:** Search your vault for specific notes.
    - **Query a Note:** Ask questions about the content of a particular note.
    - **Process a Note:** Trigger AI analysis or summarization for a note.
    - **Analyze Connections:** Explore relationships between two notes.
    - **Daily Note Toolkit:** Manage your daily journal entries.
    """)

elif st.session_state.current_mode == "Find Notes":
    query = st.text_input("What note are you looking for?", key="find_notes_input", placeholder="e.g., 'Project Titan meeting notes'")
    if st.button("Search 🔎", key="find_notes_submit"):
        if query:
            st.session_state.last_query = f"Find notes matching: {query}"
            with st.spinner("Searching your vault..."):
                result = call_api("GET", "/notes/find", params={"query": query})
                if result and "matches" in result:
                    if result["matches"]:
                        st.session_state.last_response = {
                            "message": f"Found {len(result['matches'])} note(s):",
                            "matches": result["matches"]
                        }
                        # Store matches for potential use in other modes
                        st.session_state.note_context['search_results'] = result["matches"]
                    else:
                        st.session_state.last_response = "No notes found matching your query."
                else:
                    st.session_state.last_response = "Could not complete the search."
            st.rerun() # Rerun to update the chat container

    if st.session_state.note_context.get('search_results'):
        st.markdown("---")
        st.write("You can select a found note to use in other actions:")
        selected = st.selectbox(
            "Choose a note:", 
            options=[""] + st.session_state.note_context['search_results'],
            key="search_result_selector"
        )
        if selected:
            st.session_state.note_context['selected_note_from_search'] = selected
            st.success(f"'{selected}' is now available for other actions.")


elif st.session_state.current_mode == "Query Note":
    default_note = st.session_state.note_context.get('selected_note_from_search', "")
    note_identifier = st.text_input("Which note do you want to ask about? (Name or relative path)", value=default_note, key="query_note_id", placeholder="e.g., 'My Research Notes' or 'Projects/Alpha.md'")
    question = st.text_area("What's your question about this note?", key="query_note_question", placeholder="e.g., 'What are the main conclusions?'")
    
    if st.button("Ask ObsidianGPT 💬", key="query_note_submit"):
        if note_identifier and question:
            st.session_state.last_query = f"About note '{note_identifier}': {question}"
            with st.spinner("Thinking..."):
                result = call_api("POST", "/notes/query", json_payload={"note_name_or_relative_path": note_identifier, "question": question})
                if result and "details" in result:
                    st.session_state.last_response = result["details"]
                elif result and "message" in result:
                     st.session_state.last_response = result["message"] # For simple success messages
                else:
                    st.session_state.last_response = "Sorry, I couldn't get an answer for that."
            st.rerun()
        else:
            st.warning("Please provide both the note identifier and your question.")


elif st.session_state.current_mode == "Process Note":
    default_note = st.session_state.note_context.get('selected_note_from_search', "")
    note_to_process = st.text_input("Which note should I process? (Relative path)", value=default_note, key="process_note_path", placeholder="e.g., 'Ideas/NewConcept.md'")
    if st.button("Process Note Now ⚙️", key="process_note_submit"):
        if note_to_process:
            st.session_state.last_query = f"Process the note: {note_to_process}"
            with st.spinner(f"Processing {note_to_process}..."):
                result = call_api("POST", "/notes/process", json_payload={"note_path_relative": note_to_process})
                if result:
                    st.session_state.last_response = result # Show full JSON response
                else:
                    st.session_state.last_response = f"Failed to process {note_to_process}."
            st.rerun()
        else:
            st.warning("Please specify the relative path of the note to process.")


elif st.session_state.current_mode == "Analyze Connections":
    st.markdown("Let's explore connections between two notes.")
    default_note1 = st.session_state.note_context.get('selected_note_from_search', "") # Use if only one is pre-selected
    note1 = st.text_input("Note 1 (Name or relative path):", value=default_note1, key="analyze_note1", placeholder="e.g., 'Quantum Physics Intro'")
    note2 = st.text_input("Note 2 (Name or relative path):", key="analyze_note2", placeholder="e.g., 'General Relativity Basics'")

    if st.button("Find Connections 🔗", key="analyze_connections_submit"):
        if note1 and note2:
            st.session_state.last_query = f"Analyze connections between '{note1}' and '{note2}'."
            with st.spinner("Analyzing..."):
                result = call_api("POST", "/notes/analyze-connections", json_payload={"note1_name_or_relative_path": note1, "note2_name_or_relative_path": note2})
                if result and "details" in result:
                    st.session_state.last_response = result["details"]
                elif result and "message" in result:
                     st.session_state.last_response = result["message"]
                else:
                    st.session_state.last_response = "Could not analyze connections."
            st.rerun()
        else:
            st.warning("Please provide identifiers for both notes.")

elif st.session_state.current_mode == "Daily Note Toolkit":
    st.markdown("Manage your daily notes.")
    selected_date_obj = st.date_input("Select Date for Daily Note:", value=date.today(), key="daily_toolkit_date")
    date_str_for_api = "today" if selected_date_obj == date.today() else selected_date_obj.strftime('%Y-%m-%d')

    st.caption(f"Actions below will target the daily note for: **{date_str_for_api}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Get/Create Note", key="daily_get_create_btn", use_container_width=True):
            st.session_state.last_query = f"Get or create daily note for {date_str_for_api}."
            with st.spinner("Accessing daily note..."):
                result = call_api("POST", f"/daily/{date_str_for_api}") # POST implies get_or_create
                st.session_state.last_response = result if result else "Failed to access daily note."
            st.rerun()

        if st.button("💡 Generate Summary", key="daily_summary_btn", use_container_width=True):
            st.session_state.last_query = f"Generate summary for {date_str_for_api}'s daily note."
            with st.spinner("Generating summary..."):
                result = call_api("POST", f"/daily/{date_str_for_api}/summary")
                st.session_state.last_response = result if result else "Failed to generate summary."
            st.rerun()
    with col2:
        if st.button("📝 Refresh Template", key="daily_template_btn", use_container_width=True):
            st.session_state.last_query = f"Refresh template for {date_str_for_api}'s daily note."
            with st.spinner("Refreshing template..."):
                result = call_api("POST", f"/daily/{date_str_for_api}/template")
                st.session_state.last_response = result if result else "Failed to refresh template."
            st.rerun()

        if st.button("♻️ Restructure Content", key="daily_restructure_btn", use_container_width=True):
            st.session_state.last_query = f"Restructure content for {date_str_for_api}'s daily note."
            with st.spinner("Restructuring content..."):
                result = call_api("POST", f"/daily/{date_str_for_api}/restructure")
                st.session_state.last_response = result if result else "Failed to restructure content."
            st.rerun()