"""
Pydantic models for the HackRx Document Intelligence API.

This file defines all the data models used for API requests and responses:
1. UploadResponse - Response model for document uploads
2. TaskStatusResponse - Response model for Celery task status checking
3. QueryRequest/QueryResponse - Models for individual query processing
4. HackRxRequest/HackRxResponse - Main models for the /hackrx/run endpoint

The models use Pydantic for data validation and serialization, ensuring
type safety and automatic API documentation generation.
"""

# models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Any

# --- Original Models (can be kept for testing) ---
class UploadResponse(BaseModel):
    task_id: str
    filename: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]

# --- New Models for the /hackrx/run Endpoint ---
class HackRxRequest(BaseModel):
    """
    Defines the request format for the main processing endpoint.
    """
    documents: str = Field(..., description="A URL to the document to be processed.")
    questions: List[str] = Field(..., description="A list of questions to be answered about the document.")

class HackRxResponse(BaseModel):
    """
    Defines the response format, containing a list of answers.
    """
    answers: List[str]
