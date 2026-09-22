# Workflow Comparison: LangGraph vs. Supervisor

## Execution Comparison Matrix

| Scenario | Orchestrator LLM Calls | Domain Agent LLM Calls | Total Tool Calls | Tools Executed |
| :--- | :---: | :---: | :---: | :--- |
| **General Chat** (*"Hello"*, *"Help"*) | 1 | 0 | **0** | *None* |
| **1. Order - Summary Review** | 2 | 2 | **2** | `call_order_agent`, `check_inventory_stock` |
| **1b. Order - Final Confirmation** | 2 | 2 | **3** | `call_order_agent`, `place_order`, `send_order_confirmation_email` |
| **2. Cancel Order** | 2 | 2 | **2** | `call_cancellation_agent`, `cancel_order` |
| **3. Product Enquiry** | 2 | 2 | **2** | `call_enquiry_agent`, `search_product_specs` |