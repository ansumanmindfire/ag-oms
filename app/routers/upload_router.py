"""FastAPI APIRouter for PDF specification upload and Qdrant indexing endpoints."""

from typing import List
from fastapi import APIRouter, UploadFile, File, status
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["Document Upload"])


@router.post("", status_code=status.HTTP_200_OK)
def upload_pdf(files: List[UploadFile] = File(...)):
    """Upload product specification PDF endpoint (supports single or multiple files).

    Extracts text from uploaded PDF(s), chunks text, generates Dense + Sparse vectors,
    and indexes them into Qdrant Vector DB for Enquiry Agent retrieval.
    """
    return UploadService.index_pdfs(files)

