from langchain_core.messages import HumanMessage
from deepeval import assert_test
from deepeval.test_case import Turn, ConversationalTestCase
from deepeval.metrics import RoleAdherenceMetric

from app.graph.subgraphs.cancellation_subgraph import cancellation_subgraph
from evals.judge import eval_judge
from evals.test_agent import extract_tools
from app.prompts import CANCELLATION_AGENT_SYSTEM_PROMPT


def test_multi_turn_cancellation_flow():

    # Turn 1: User provides Order ID and Email
    turn1_input = "I want to cancel order 32kjb431433214. My email is ansumainpanda@gmail.com"
    res1 = cancellation_subgraph.invoke({"messages": [HumanMessage(content=turn1_input)]})

    turn1_tools = extract_tools(res1)
    turn1_output = res1["messages"][-1].content

    turn1_user = Turn(role="user", content=turn1_input)
    turn1_agent = Turn(role="assistant", content=turn1_output, tools_called=turn1_tools)

    # Turn 2: User confirms cancellation
    turn2_input = "I confirm"
    res2 = cancellation_subgraph.invoke(
        {"messages": res1["messages"] + [HumanMessage(content=turn2_input)]}
    )

    # new_turn2_messages = res2["messages"][len(res1["messages"]):]
    turn2_tools = extract_tools(res2)
    turn2_output = res2["messages"][-1].content

    turn2_user = Turn(role="user", content=turn2_input)
    turn2_agent = Turn(role="assistant", content=turn2_output, tools_called=turn2_tools)

    # Conversational Test Case
    conversation = ConversationalTestCase(
        turns=[turn1_user, turn1_agent, turn2_user, turn2_agent],
        chatbot_role=CANCELLATION_AGENT_SYSTEM_PROMPT,
    )

    metric = RoleAdherenceMetric(threshold=0.7, model=eval_judge)
    assert_test(conversation, [metric])
