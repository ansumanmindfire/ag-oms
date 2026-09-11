"""Streamlit web application interface for Agentic Order Management System (AG-oms)."""

import os
import uuid
import requests
import streamlit as st

# Backend REST API Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Streamlit Page Configuration
st.set_page_config(
    page_title="AG-oms | Agentic Order Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session State Initialization
if "session_id" not in st.session_state or not st.session_state.session_id:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Navigation & Setup
with st.sidebar:
    st.title("📦 AG-oms Dashboard")
    st.caption("Agentic Order Management System")
    st.divider()

    # Backend Connection Status
    st.subheader("System Status")
    try:
        health_res = requests.get(f"{BACKEND_API_URL}/", timeout=5)
        if health_res.status_code == 200:
            st.success("🟢 Connected to AG-oms Backend API")
        else:
            st.warning(f"🟡 Backend returned status: {health_res.status_code}")
    except requests.exceptions.RequestException:
        st.error("🔴 Backend API Offline")

    st.divider()

    # Upload Order Specifications PDF
    st.subheader("Upload Product Specs")
    st.caption("Index PDF specifications for product enquiries")
    uploaded_files = st.file_uploader(
        "Choose PDF spec file(s)",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.button("Upload & Index Specs", use_container_width=True):
        with st.spinner("Extracting text and indexing into Qdrant..."):
            try:
                files_payload = [
                    ("files", (f.name, f.getvalue(), "application/pdf"))
                    for f in uploaded_files
                ]
                res = requests.post(
                    f"{BACKEND_API_URL}/api/v1/upload",
                    files=files_payload,
                    timeout=60,
                )

                if res.status_code == 200:
                    st.success("Successfully indexed PDF specifications!")
                    st.json(res.json())
                else:
                    st.error(f"Upload failed ({res.status_code}): {res.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

    st.divider()

    # Active Session Information
    st.subheader("Session Controls")
    st.code(f"Session ID: {st.session_state.session_id}", language="text")

    if st.button("Clear Chat Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# Main Application Interface
st.title("🤖 Order Management Assistant")
st.markdown(
    "Welcome! You can place orders, cancel orders, track status, or inquire about product specifications."
)

# Quick Action Prompt Helper Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🛍️ Sample Order", use_container_width=True):
        prompt_preset = "I want to order 2 units of Laptop with customer email alice@example.com."
        st.session_state.preset_prompt = prompt_preset
with col2:
    if st.button("🔍 Check Specs", use_container_width=True):
        prompt_preset = "What are the specs and battery life for the Laptop?"
        st.session_state.preset_prompt = prompt_preset
with col3:
    if st.button("❌ Cancel Order", use_container_width=True):
        prompt_preset = "Please cancel my order #1."
        st.session_state.preset_prompt = prompt_preset

st.divider()

# Render Chat History
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.write(msg["content"])

# Check for Preset Prompt
initial_input = st.session_state.pop("preset_prompt", None)

# Chat Input Handler
if prompt := (st.chat_input("How can I assist with your order today?") or initial_input):
    # Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    # Query Backend API
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Processing request via Master Orchestrator..."):
            try:
                payload = {
                    "prompt": prompt,
                    "session_id": st.session_state.session_id,
                }
                chat_res = requests.post(
                    f"{BACKEND_API_URL}/api/v1/query",
                    json=payload,
                    timeout=60,
                )

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
