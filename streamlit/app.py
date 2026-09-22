import json
import requests
import streamlit as st

# Backend REST API Endpoints Configuration
BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/v1/upload"
QUERY_STREAM_ENDPOINT = f"{BASE_URL}/api/v1/query/stream"

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
                    st.success("Product Specifications successfully added.")
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
st.markdown("Place/ Cancel/ Enquire orders.")
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
        payload = {
            "prompt": prompt,
            "session_id": st.session_state.session_id,
        }

        try:
            response = requests.post(QUERY_STREAM_ENDPOINT, json=payload, stream=True)

            if response.status_code == 200:
                status_container = st.status("Thinking...", expanded=True)
                message_placeholder = st.empty()

                def stream_tokens():
                    has_tokens = False
                    for line in response.iter_lines():
                        if not line:
                            continue
                        decoded = line.decode("utf-8") if isinstance(line, bytes) else line
                        if not decoded.startswith("data: "):
                            continue
                        event = json.loads(decoded[6:].strip())

                        if event.get("type") == "session":
                            st.session_state.session_id = event.get("session_id")

                        elif event.get("type") == "status":
                            status_container.write(event.get("content", ""))

                        elif event.get("type") == "token":
                            if not has_tokens:
                                has_tokens = True
                                status_container.update(label="Agent reasoning complete", state="complete", expanded=False)
                            yield event.get("content", "")

                    if not has_tokens:
                        status_container.update(label="Agent reasoning complete", state="complete", expanded=False)

                full_response = ""
                for token in stream_tokens():
                    full_response += token
                    message_placeholder.markdown(full_response + "|")
                message_placeholder.markdown(full_response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                })
            else:
                try:
                    err_msg = response.json().get("detail", response.text)
                except (ValueError, AttributeError):
                    err_msg = response.text
                st.error(f"API Error ({response.status_code}): {err_msg}")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")
