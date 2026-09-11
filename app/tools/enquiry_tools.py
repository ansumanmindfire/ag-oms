"""LangChain custom tool for searching product technical specifications from Qdrant Hybrid Vector DB."""

import json
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.qdrant_service import QdrantVectorService
from app.config import logger


class SearchProductSpecsInput(BaseModel):
    """Input schema for searching product technical specifications."""
    query: str = Field(..., description="Natural language enquiry query about product specs, smart features, Wi-Fi, noise, energy, or warranty (e.g. 'smart washer wifi features and warranty')")


class SearchProductSpecsTool(BaseTool):
    """Tool for retrieving relevant product specification context snippets from Qdrant Vector DB using Hybrid Search."""

    name: str = "search_product_specs"
    description: str = (
        "Useful for retrieving product technical specifications, smart features, Wi-Fi capabilities, "
        "energy ratings, noise levels, and warranty details from Qdrant Vector DB. "
        "Returns a list of matching context snippets with keys: 'text', 'source', 'page_number', and 'score'."
    )
    args_schema: Type[BaseModel] = SearchProductSpecsInput

    def _run(self, query: str) -> str:
        """Synchronous execution of Qdrant Hybrid Search."""
        logger.info(f"Tool execution [search_product_specs]: query='{query}'")
        try:
            documents = QdrantVectorService.hybrid_search(query=query, top_k=4)
            if not documents:
                return json.dumps({
                    "results": [],
                    "message": "No relevant product specification documents found in Qdrant Vector DB. Please upload specification PDFs via /api/v1/upload."
                })

            formatted_results = [
                {
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", ""),
                    "page_number": doc.metadata.get("page_number", 1),
                    "score": doc.metadata.get("score", 0.0),
                }
                for doc in documents
            ]
            return json.dumps(formatted_results, indent=2)
        except Exception as err:
            logger.error(f"Error in SearchProductSpecsTool: {err}")
            return json.dumps({"error": str(err)})

