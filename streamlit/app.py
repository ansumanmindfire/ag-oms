import json
import requests
import streamlit as st

# Backend REST API Endpoints Configuration
BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/v1/upload"
QUERY_ENDPOINT = f"{BASE_URL}/api/v1/query"
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
        payload = {
            "prompt": prompt,
            "session_id": st.session_state.session_id,
        }

        try:
            response = requests.post(QUERY_STREAM_ENDPOINT, json=payload, stream=True, timeout=90)

            if response.status_code == 200:

                def stream_tokens():
                    for raw_line in response.iter_lines():
                        if not raw_line:
                            continue
                        decoded_line = raw_line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            try:
                                event = json.loads(decoded_line[6:].strip())

                                if event.get("type") == "session":
                                    st.session_state.session_id = event.get("session_id")

                                elif event.get("type") == "token":
                                    yield event.get("content", "")

                            except Exception:
                                continue

                full_response = st.write_stream(stream_tokens())

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response if full_response else "",
                })
            else:
                err_msg = (
                    response.json().get("detail", response.text)
                    if response.headers.get("content-type") == "application/json"
                    else response.text
                )
                st.error(f"API Error ({response.status_code}): {err_msg}")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")

