"""Upload Service for processing uploaded PDF specification files and indexing into Qdrant."""

import io
from typing import Dict, Any, List
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter



from app.services.qdrant_service import QdrantVectorService
from app.config import logger


class UploadService:
    """Service handling PDF specification extraction, text chunking, and Qdrant vector indexing."""

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    @classmethod
    def index_pdfs(cls, files: List[UploadFile]) -> Dict[str, Any]:
        """Extract text from uploaded PDF files, chunk into Documents, and index into Qdrant Hybrid Vector DB.


        Args:
            files (List[UploadFile]): List of FastAPI uploaded PDF files.

        Returns:
            Dict[str, Any]: Payload dictionary summarizing status and indexed chunks count.
        """
        if not files:
            raise HTTPException(status_code=400, detail="No files provided for upload.")

        all_page_documents: List[Document] = []
        processed_files: List[Dict[str, Any]] = []

        for file in files:
            if not file.filename.lower().endswith(".pdf"):
                logger.warning(f"Skipping non-PDF file: '{file.filename}'")
                continue

            logger.info(f"Processing uploaded PDF specification: '{file.filename}'")

            try:
                content_bytes = file.file.read()
                pdf_file_obj = io.BytesIO(content_bytes)
                reader = PdfReader(pdf_file_obj)

                file_page_docs: List[Document] = []
                for page_idx, page in enumerate(reader.pages):
                    page_num = page_idx + 1
                    page_text = (page.extract_text() or "").strip()
                    if page_text:
                        file_page_docs.append(
                            Document(
                                page_content=page_text,
                                metadata={"source": file.filename, "page_number": page_num},
                            )
                        )

                all_page_documents.extend(file_page_docs)
                processed_files.append({
                    "filename": file.filename,
                    "pages": len(reader.pages),
                    "page_docs": len(file_page_docs),
                })
            except Exception as err:
                logger.error(f"Failed to process uploaded PDF '{file.filename}': {err}")

        if not all_page_documents:
            raise HTTPException(status_code=400, detail="Could not extract readable text from uploaded PDF file(s).")

        # Split page documents into chunks using RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=cls.CHUNK_SIZE,
            chunk_overlap=cls.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks: List[Document] = text_splitter.split_documents(all_page_documents)

        points_count = QdrantVectorService.upsert_documents(chunks)

        return {
            "success": True,
            "total_files": len(processed_files),
            "files": processed_files,
            "total_chunks_indexed": points_count,
            "message": f"Successfully indexed {points_count} text chunks from {len(processed_files)} PDF file(s) into Qdrant Hybrid Vector DB.",
        }


