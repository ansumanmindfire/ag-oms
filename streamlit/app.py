"""Streamlit web application interface for Agentic Order Management System (AG-oms)."""

import requests
import streamlit as st

# Backend REST API Endpoints Configuration
BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/v1/upload"
QUERY_ENDPOINT = f"{BASE_URL}/api/v1/query"

# Streamlit Page Configuration
st.set_page_config(
    page_title="AG-oms | Order Management System",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session State Initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Navigation & Management
with st.sidebar:

    # Backend Connection Status
    st.subheader("System Status")
    try:
        health_res = requests.get(HEALTH_ENDPOINT, timeout=5)
        if health_res.status_code == 200:
            st.success("Connected to Backend API")
        else:
            st.warning(f"Backend returned status: {health_res.status_code}")
    except requests.exceptions.RequestException:
        st.error("Backend API Offline")

    st.divider()

    # Upload Product Specifications PDF
    st.subheader("Upload Product Specs")
    uploaded_files = st.file_uploader(
        "Select documents",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.button("Upload", use_container_width=True):
        with st.spinner("Updating the product specifications..."):
            try:
                files_payload = [
                    ("files", (f.name, f.getvalue(), "application/pdf"))
                    for f in uploaded_files
                ]
                res = requests.post(UPLOAD_ENDPOINT, files=files_payload)

                if res.status_code == 200:
                    st.success(f"Product Specifications successfully added.")
                else:
                    st.error(f"Upload failed ({res.status_code}): {res.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

    st.divider()

    # Session Management
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

# Main Chat Interface
st.title("Order Management Assistant")
st.markdown(
    "Place/ Cancel/ Enquire orders."
)
st.divider()

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat Input Handler
if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing request..."):
            try:
                payload = {
                    "prompt": prompt,
                    "session_id": st.session_state.session_id,
                }
                chat_res = requests.post(QUERY_ENDPOINT, json=payload)

                if chat_res.status_code == 200:
                    data = chat_res.json()
                    answer_text = data.get("answer", "No response received.")
                    returned_session_id = data.get("session_id")

                    if returned_session_id:
                        st.session_state.session_id = returned_session_id

                    st.write(answer_text)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer_text,
                    })
                else:
                    err_msg = chat_res.json().get("detail", chat_res.text) if chat_res.headers.get("content-type") == "application/json" else chat_res.text
                    st.error(f"API Error ({chat_res.status_code}): {err_msg}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")
