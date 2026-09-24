from langchain_core.messages import HumanMessage
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import ToolCorrectnessMetric

from app.graph.subgraphs.cancellation_subgraph import cancellation_subgraph
from app.graph.subgraphs.order_subgraph import order_subgraph
from evals.judge import eval_judge


def extract_tools(result):
    """Helper to extract ToolCall objects from LangGraph message history."""
    tools = []
    for msg in result.get("messages", []):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for call in msg.tool_calls:
                tools.append(
                    ToolCall(
                        name=call["name"],
                        input_parameters=call["args"],
                    )
                )
    return tools


def test_cancellation_agent_tool_correctness():
    query = "CONFIRMED: Cancel order 12b213bhj213hb14 for customer email ansumainpanda@gmail.com"

    # Run Cancellation Subgraph
    result = cancellation_subgraph.invoke({"messages": [HumanMessage(content=query)]})
    actual_tools = extract_tools(result)
    actual_output = result["messages"][-1].content

    # Expected tool & arguments
    expected_tools = [
        ToolCall(
            name="cancel_order",
            input_parameters={"order_id": "12b213bhj213hb14", "customer_email": "ansumainpanda@gmail.com"},
        )
    ]

    # Assert Tool & Argument Correctness
    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        tools_called=actual_tools,
        expected_tools=expected_tools,
    )
    metric = ToolCorrectnessMetric(threshold=0.7, model=eval_judge)
    assert_test(test_case, [metric])


def test_order_agent_tool_correctness():
    query = "Can you check if we have 2 units of samsung phone in stock?"

    # Run Order Subgraph
    result = order_subgraph.invoke({"messages": [HumanMessage(content=query)]})
    actual_tools = extract_tools(result)
    actual_output = result["messages"][-1].content

    # Expected tool & arguments
    expected_tools = [
        ToolCall(
            name="search_inventory_products",
            input_parameters={"query": "phone"}
        ),
        ToolCall(
            name="check_inventory_stock",
            input_parameters={"product_id": "PROD-004", "quantity": 2},
        )
    ]

    # Assert Tool & Argument Correctness
    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        tools_called=actual_tools,
        expected_tools=expected_tools,
    )
    metric = ToolCorrectnessMetric(threshold=0.7, model=eval_judge)
    assert_test(test_case, [metric])
