"""
API routes for NyayaSetu AI Platform
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.schemas.ai import (
    DeidentificationResponse,
    ErrorResponse,
    DocumentFormat
)
from app.ai.service import get_deidentification_service
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ai", tags=["AI Services"])


@router.post(
    "/deidentify",
    response_model=DeidentificationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="De-identify a document",
    description="Upload a document (PDF, JPG, PNG) and receive de-identified structured data"
)
async def deidentify_document(
    file: UploadFile = File(..., description="Document file to process")
) -> DeidentificationResponse:
    """
    De-identify a document and extract structured data
    
    This endpoint:
    1. Accepts a document upload (PDF, JPG, JPEG, PNG)
    2. Processes it using AWS Bedrock Nova model
    3. Extracts information following privacy rules
    4. Returns structured JSON with redacted PII
    
    Args:
        file: Uploaded document file
        
    Returns:
        DeidentificationResponse with extracted and de-identified data
        
    Raises:
        HTTPException: If file is invalid or processing fails
    """
    try:
        # Validate file extension
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file bytes
        file_bytes = await file.read()
        
        # Validate file size
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )
        
        # Normalize format for Bedrock API
        document_format = file_extension
        if file_extension == "jpg":
            document_format = "jpeg"
        
        logger.info(f"Processing document: {file.filename} ({len(file_bytes)} bytes)")
        
        # Get de-identification service
        service = get_deidentification_service()
        
        # Process document
        result = await service.process_document(
            document_bytes=file_bytes,
            document_format=document_format,
            document_name=file.filename
        )
        
        logger.info(f"Document processed successfully: {file.filename}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the AI service is running"
)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Status message
    """
    return {
        "status": "healthy",
        "service": "NyayaSetu AI - De-identification Service",
        "model": settings.BEDROCK_MODEL_ID
    }


@router.get(
    "/supported-formats",
    summary="Get supported document formats",
    description="List all supported document formats for de-identification"
)
async def get_supported_formats():
    """
    Get list of supported document formats
    
    Returns:
        List of supported formats
    """
    return {
        "supported_formats": settings.ALLOWED_EXTENSIONS,
        "max_file_size_mb": settings.MAX_UPLOAD_SIZE / (1024 * 1024)
    }
