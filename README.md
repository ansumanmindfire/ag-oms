# Agentic Order Management System (AG-oms)

A fully agentic order management system built with **FastAPI**, **LangChain**, **Google Gemini**, **Qdrant Vector DB**, **SQLite**, and **Streamlit**.

## Architecture Overview
- **Master Orchestrator Agent**: Routes user queries to specialized agents (Order, Cancellation, Enquiry RAG).
- **Order Agent**: Handles order creation, stock availability check, inventory update, audit logging, and email notification.
- **Cancellation Agent**: Handles order cancellation, inventory restoration, audit logging, and email notification.
- **Enquiry Agent**: Intelligent product specification RAG querying Qdrant Hybrid Search.
- **Streamlit Frontend**: Interactive web dashboard for chat assistant, inventory management, orders, and audit logs.

## Setup & Running
1. Install dependencies:
   ```bash
   poetry install
   ```
2. Run FastAPI Backend:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```
3. Run Streamlit Frontend:
   ```bash
   poetry run streamlit run streamlit/app.py
   ```
