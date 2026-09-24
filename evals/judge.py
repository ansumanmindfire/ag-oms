"""Custom LLM Judge for DeepEval."""
from deepeval.models.base_model import DeepEvalBaseLLM
from app.llm import get_llm, extract_text_content


class DeepEvalJudge(DeepEvalBaseLLM):
    def __init__(self):
        self._llm = get_llm(max_tokens=4096)

    def load_model(self):
        return self._llm

    def generate(self, prompt: str) -> str:
        res = self._llm.invoke(prompt)
        return extract_text_content(res.content)

    async def a_generate(self, prompt: str) -> str:
        res = await self._llm.ainvoke(prompt)
        return extract_text_content(res.content)

    def get_model_name(self) -> str:
        return "ag-oms-judge"


eval_judge = DeepEvalJudge()
