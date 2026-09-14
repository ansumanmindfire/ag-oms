"""Upload Service for processing uploaded PDF specification files and indexing into Qdrant."""

import io
import re
from typing import Dict, Any, List
from fastapi import UploadFile, HTTPException
import pdfplumber
from langchain_core.documents import Document

from app.services.qdrant_service import QdrantVectorService
from app.config import logger


class UploadService:
    """Service handling PDF specification extraction and Qdrant vector indexing."""

    @classmethod
    def index_pdfs(cls, files: List[UploadFile], category: str = None) -> Dict[str, Any]:
        """Extract text from uploaded PDF files, chunk into Documents, and index into Qdrant Hybrid Vector DB.

        Args:
            files (List[UploadFile]): List of FastAPI uploaded PDF files.
            category (str, optional): Product category (e.g., 'smartphones', 'laptops'). Defaults to 'general'.

        Returns:
            Dict[str, Any]: Payload dictionary summarizing status and indexed chunks count.
        """
        if not files:
            raise HTTPException(status_code=400, detail="No files provided for upload.")

        # Clean category or default to 'general'
        doc_category = category.strip().lower() if category and category.strip() else "general"

        all_documents: List[Document] = []
        processed_files: List[Dict[str, Any]] = []

        for file in files:
            if not file.filename.lower().endswith(".pdf"):
                logger.warning(f"Skipping non-PDF file: '{file.filename}'")
                continue

            logger.info(f"Processing uploaded PDF specification: '{file.filename}' (Category: '{doc_category}')")

            try:
                content_bytes = file.file.read()
                pdf_file_obj = io.BytesIO(content_bytes)

                with pdfplumber.open(pdf_file_obj) as pdf:
                    full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

                    # Extract each product card (Product Title directly followed by 'Brand: <name>')
                    matches = list(re.finditer(r"(?:^|\n)([^\n]+)\nBrand:\s*([^\n]+)", full_text))

                    file_chunks: List[Document] = []
                    for i, m in enumerate(matches):
                        start = m.start()
                        end = matches[i + 1].start() if (i + 1 < len(matches)) else len(full_text)
                        product_text = full_text[start:end].strip()

                        file_chunks.append(
                            Document(
                                page_content=product_text,
                                metadata={
                                    "source": file.filename,
                                    "category": doc_category,
                                    "product_name": m.group(1).strip(),
                                    "brand": m.group(2).strip(),
                                },
                            )
                        )

                    all_documents.extend(file_chunks)
                    processed_files.append({
                        "filename": file.filename,
                        "category": doc_category,
                        "pages": len(pdf.pages),
                        "chunks_extracted": len(file_chunks),
                    })
            except Exception as err:
                logger.error(f"Failed to process uploaded PDF '{file.filename}': {err}")

        if not all_documents:
            raise HTTPException(status_code=400, detail="Could not extract readable text from uploaded PDF file(s).")

        points_count = QdrantVectorService.upsert_documents(all_documents)

        return {
            "success": True,
            "total_files": len(processed_files),
            "files": processed_files,
            "total_chunks_indexed": points_count,
            "message": f"Successfully indexed {points_count} specification chunks from {len(processed_files)} PDF file(s) into Qdrant Hybrid Vector DB.",
        }


