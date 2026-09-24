import pytest
from langchain_core.messages import HumanMessage
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualRelevancyMetric

from app.services.qdrant_service import QdrantVectorService
from app.graph.subgraphs.enquiry_subgraph import enquiry_subgraph
from app.llm import extract_text_content
from evals.judge import eval_judge


def test_rag_evaluation():
    query = "Tell me about the specifications of the samsung phone?"

    try:
        docs = QdrantVectorService.hybrid_search(query=query, top_k=3)
    except Exception as err:
        pytest.fail(f"Could not connect to Qdrant at - {err}")

    if not docs:
        pytest.skip("Add specifications PDFs")

    retrieval_context = [doc.page_content for doc in docs]

    result = enquiry_subgraph.invoke({"messages": [HumanMessage(content=query)]})
    actual_output = extract_text_content(result["messages"][-1].content)

    assert actual_output, "Enquiry agent returned an empty response."

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )

    relevancy = AnswerRelevancyMetric(threshold=0.7, model=eval_judge)
    # faithfulness = FaithfulnessMetric(threshold=0.7, model=eval_judge)
    # contextual_relevancy = ContextualRelevancyMetric(threshold=0.7, model=eval_judge)
    assert_test(test_case, [relevancy])
