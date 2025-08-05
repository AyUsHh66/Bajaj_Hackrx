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
