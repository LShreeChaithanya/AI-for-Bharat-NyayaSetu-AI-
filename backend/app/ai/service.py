"""
AI Service for document de-identification using AWS Bedrock
Uses Converse API for document + text (Nova document understanding).
"""
import os
import re
import boto3
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.config import settings
from app.schemas.ai import (
    DeidentificationResponse,
    ExtractedData,
    DeidentificationMetadata,
    DocumentQuality
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _sanitize_document_name(name: str) -> str:
    """Sanitize document name for Bedrock Converse: alphanumeric, space, hyphen, parentheses, square brackets only; no consecutive spaces."""
    if not name or not name.strip():
        return "document"
    # Bedrock allows only: alphanumeric, whitespace, hyphens, parentheses, square brackets
    s = name.replace("_", "-").replace(".", "-")
    s = re.sub(r"[^a-zA-Z0-9\s\-()\[\]]", "-", s)
    s = re.sub(r"[\s\-]+", " ", s).strip()
    if not s:
        return "document"
    return s[:255]


class DeidentificationService:
    """
    Service for de-identifying documents using AWS Bedrock Nova model
    """
    
    def __init__(self):
        """Initialize AWS Bedrock client using API key (bearer token) from env."""
        token = (settings.AWS_BEARER_TOKEN_BEDROCK or "").strip()
        if not token:
            raise ValueError(
                "AWS_BEARER_TOKEN_BEDROCK is not set. "
                "Set it in .env (or environment) to use the Bedrock API key for authentication."
            )
        # Bedrock API key: boto3 uses this env var for auth (no access key/secret needed)
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION,
        )
        self.model_id = settings.BEDROCK_MODEL_ID
        self.system_prompt = self._load_system_prompt()
        if not hasattr(self.client, "converse"):
            raise RuntimeError(
                "Bedrock client has no 'converse' method. "
                "Install boto3>=1.34.131 (e.g. pip install 'boto3>=1.34.131')."
            )
        logger.info(f"DeidentificationService initialized with model: {self.model_id}")
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file (path relative to this package so it works from any cwd)."""
        try:
            configured = (settings.DEIDENTIFICATION_PROMPT_PATH or "").strip()
            if configured:
                prompt_path = Path(configured)
                if prompt_path.exists():
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        system_prompt = f.read()
                    logger.info("System prompt loaded successfully")
                    return system_prompt
            # Default: resolve relative to backend/app/ai so it works when cwd is backend or project root
            prompt_path = Path(__file__).resolve().parent / "prompts" / "system" / "deidentification.txt"
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
            logger.info("System prompt loaded successfully")
            return system_prompt
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            raise
    
    async def process_document(
        self,
        document_bytes: bytes,
        document_format: str,
        document_name: str
    ) -> DeidentificationResponse:
        """
        Process a document and return de-identified data
        
        Args:
            document_bytes: Raw document bytes
            document_format: Format of document (pdf, jpg, jpeg, png)
            document_name: Name of the document
            
        Returns:
            DeidentificationResponse with extracted and de-identified data
            
        Raises:
            Exception: If processing fails
        """
        try:
            logger.info(f"Processing document: {document_name} (format: {document_format})")
            safe_name = _sanitize_document_name(document_name) or "document"

            # Converse API: document + text (Nova document understanding)
            response = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "document": {
                                    "format": document_format,
                                    "name": safe_name,
                                    "source": {"bytes": document_bytes},
                                }
                            },
                            {"text": self.system_prompt},
                        ],
                    }
                ],
            )

            # Extract the response text from Converse output
            response_text = response["output"]["message"]["content"][0]["text"]
            logger.info("Received response from Bedrock model")
            
            # Parse JSON response
            parsed_response = self._parse_response(response_text)
            
            # Convert to Pydantic model
            deident_response = self._convert_to_response_model(parsed_response)
            
            logger.info(f"Document processed successfully: {document_name}")
            return deident_response
            
        except Exception as e:
            logger.error(f"Error processing document {document_name}: {e}")
            raise
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the JSON response from the model
        
        Args:
            response_text: Raw text response from model
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If response is not valid JSON
        """
        try:
            # Try to parse as JSON directly
            parsed = json.loads(response_text)
            return parsed
        except json.JSONDecodeError:
            # If response contains markdown code blocks, extract JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                parsed = json.loads(json_str)
                return parsed
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                parsed = json.loads(json_str)
                return parsed
            else:
                raise ValueError("Response is not valid JSON")
    
    def _convert_to_response_model(self, parsed_data: Dict[str, Any]) -> DeidentificationResponse:
        """
        Convert parsed JSON to Pydantic response model
        
        Args:
            parsed_data: Parsed JSON dictionary
            
        Returns:
            DeidentificationResponse model
        """
        # Extract data section
        extracted_data = ExtractedData(**parsed_data.get("extracted_data", {}))
        
        # Extract metadata section
        metadata_dict = parsed_data.get("metadata", {})
        
        # Ensure processing_timestamp is datetime
        if isinstance(metadata_dict.get("processing_timestamp"), str):
            metadata_dict["processing_timestamp"] = datetime.fromisoformat(
                metadata_dict["processing_timestamp"].replace("Z", "+00:00")
            )
        else:
            metadata_dict["processing_timestamp"] = datetime.utcnow()
        
        # Ensure document_quality is enum
        if isinstance(metadata_dict.get("document_quality"), str):
            metadata_dict["document_quality"] = DocumentQuality(metadata_dict["document_quality"])
        else:
            metadata_dict["document_quality"] = DocumentQuality.MEDIUM
        
        metadata = DeidentificationMetadata(**metadata_dict)
        
        return DeidentificationResponse(
            extracted_data=extracted_data,
            metadata=metadata
        )


# Global service instance
_deidentification_service: Optional[DeidentificationService] = None


def get_deidentification_service() -> DeidentificationService:
    """
    Get or create the global DeidentificationService instance
    
    Returns:
        DeidentificationService instance
    """
    global _deidentification_service
    if _deidentification_service is None:
        _deidentification_service = DeidentificationService()
    return _deidentification_service
