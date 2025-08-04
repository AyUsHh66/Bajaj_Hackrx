from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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
    sources: List

# A generic Pydantic model for handling any kind of table data.
# This replaces the overly specific FinancialSummary model.
class GeneralTableContent(BaseModel):
    """
    A generic model to hold extracted table data as a list of rows,
    where each row is a dictionary. This is useful for structured extraction
    from tables if needed in the future.
    """
    rows: List = Field(
        description="A list of rows, where each row is a dictionary mapping column headers to cell values."
    )
