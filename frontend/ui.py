import streamlit as st
import requests
import os

try:
    BACKEND_URL = st.secrets["BACKEND_URL"]
except (FileNotFoundError, KeyError):
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("🏥 AHS Triage Agent")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add the initial prompt from the bot
    st.session_state.messages.append({"role": "assistant", "content": "Hi there. To find the best facility for you, please tell me your current address (or just your city) and what medical issue you are dealing with."})

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("I am in..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send request to FastAPI backend
    with st.spinner("Checking wait times..."):
        try:
            response = requests.post(f"{BACKEND_URL}/api/chat", json={"message": prompt})
            response.raise_for_status()
            agent_reply = response.json().get("response")
        except Exception as e:
            agent_reply = f"Error connecting to backend: {e}"

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(agent_reply)
    st.session_state.messages.append({"role": "assistant", "content": agent_reply})