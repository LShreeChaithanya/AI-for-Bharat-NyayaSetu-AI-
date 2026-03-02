"""
Pydantic schemas for AI-related API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class DocumentFormat(str, Enum):
    """Supported document formats"""
    PDF = "pdf"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"


class DocumentType(str, Enum):
    """Types of documents that can be processed"""
    AADHAAR = "Aadhaar Card"
    PAN = "PAN Card"
    INCOME_CERTIFICATE = "Income Certificate"
    CASTE_CERTIFICATE = "Caste Certificate"
    DOMICILE_CERTIFICATE = "Domicile Certificate"
    DISABILITY_CERTIFICATE = "Disability Certificate"
    RATION_CARD = "Ration Card"
    VOTER_ID = "Voter ID"
    DRIVING_LICENSE = "Driving License"
    PASSPORT = "Passport"
    EDUCATION_CERTIFICATE = "Education Certificate"
    OTHER = "Other"


class DocumentQuality(str, Enum):
    """Document quality assessment"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DeidentificationRequest(BaseModel):
    """Request schema for document de-identification"""
    document_name: str = Field(..., description="Name of the document")
    document_format: DocumentFormat = Field(..., description="Format of the document (pdf, jpg, jpeg, png)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_name": "aadhaar_card.pdf",
                "document_format": "pdf"
            }
        }


class ExtractedData(BaseModel):
    """Schema for extracted and de-identified data"""
    holder_name: Optional[str] = Field(None, description="Redacted holder name")
    father_name: Optional[str] = Field(None, description="Redacted father's name")
    mother_name: Optional[str] = Field(None, description="Redacted mother's name")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (DD/MM/YYYY)")
    age: Optional[int] = Field(None, description="Age in years")
    gender: Optional[str] = Field(None, description="Gender (Male/Female/Other)")
    social_category: Optional[str] = Field(None, description="Social category (General/OBC/SC/ST/EWS)")
    marital_status: Optional[str] = Field(None, description="Marital status")
    state: Optional[str] = Field(None, description="State name")
    district: Optional[str] = Field(None, description="District name")
    address: Optional[str] = Field(None, description="Redacted full address")
    phone: Optional[str] = Field(None, description="Redacted phone number")
    email: Optional[str] = Field(None, description="Redacted email")
    aadhaar_number: Optional[str] = Field(None, description="Redacted Aadhaar number")
    pan_number: Optional[str] = Field(None, description="Redacted PAN number")
    annual_family_income: Optional[float] = Field(None, description="Annual family income")
    income_slab: Optional[str] = Field(None, description="Income category")
    disability_status: Optional[str] = Field(None, description="Disability status (Yes/No)")
    disability_percentage: Optional[float] = Field(None, description="Disability percentage")
    bpl_status: Optional[str] = Field(None, description="Below Poverty Line status")
    occupation: Optional[str] = Field(None, description="Occupation")
    employment_status: Optional[str] = Field(None, description="Employment status")
    education_qualification: Optional[str] = Field(None, description="Education qualification")
    document_specific_fields: Optional[Dict[str, Any]] = Field(None, description="Document-specific fields")


class DeidentificationMetadata(BaseModel):
    """Metadata about the de-identification process"""
    document_type: str = Field(..., description="Type of document processed")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    language_detected: Optional[str] = Field(None, description="Detected language")
    processing_timestamp: datetime = Field(..., description="Processing timestamp")
    redacted_fields_count: int = Field(..., description="Number of redacted fields")
    preserved_fields_count: int = Field(..., description="Number of preserved fields")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    document_quality: DocumentQuality = Field(..., description="Document quality assessment")


class DeidentificationResponse(BaseModel):
    """Response schema for document de-identification"""
    extracted_data: ExtractedData = Field(..., description="Extracted and de-identified data")
    metadata: DeidentificationMetadata = Field(..., description="Processing metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "extracted_data": {
                    "holder_name": "[REDACTED_HOLDER_NAME]",
                    "date_of_birth": "15/08/1995",
                    "age": 28,
                    "gender": "Male",
                    "state": "Karnataka",
                    "district": "Bangalore Urban",
                    "address": "[REDACTED_FULL_ADDRESS]",
                    "aadhaar_number": "[REDACTED_AADHAAR_NUMBER]"
                },
                "metadata": {
                    "document_type": "Aadhaar Card",
                    "confidence_score": 0.98,
                    "language_detected": "English",
                    "processing_timestamp": "2024-01-15T10:30:00Z",
                    "redacted_fields_count": 4,
                    "preserved_fields_count": 4,
                    "warnings": [],
                    "document_quality": "High"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Document processing failed",
                "detail": "Unsupported document format",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
