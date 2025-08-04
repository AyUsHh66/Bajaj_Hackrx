# main.py

import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from celery.result import AsyncResult
from pathlib import Path

from models import UploadResponse, TaskStatusResponse, QueryRequest, QueryResponse
from tasks import process_document_task
from retrieval_service import RetrievalService

# Create a directory for temporary file uploads
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Multimodal Document Intelligence Platform",
    description="API for uploading and querying complex documents.",
)

# --- Dependency Injection ---
# This function creates the RetrievalService only when it's needed (i.e., for a /query request).
# This prevents the server from crashing on startup if the index doesn't exist yet.
def get_retrieval_service():
    # We can add caching here in the future if needed
    return RetrievalService()

@app.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a document upload and queues it for processing.
    """
    try:
        temp_file_path = UPLOAD_DIR / file.filename
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        task = process_document_task.delay(str(temp_file_path), file.filename)

        return {
            "task_id": task.id,
            "filename": file.filename,
            "message": "File uploaded successfully. Processing has started."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/tasks/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """Polls for the status of a background task."""
    task_result = AsyncResult(task_id)
    result = None
    if task_result.ready():
        if task_result.successful():
            result = task_result.get()
        else:
            result = str(task_result.info)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": result
    }

@app.post("/query", response_model=QueryResponse)
def query_documents(
    request: QueryRequest,
    service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Accepts a query and returns an answer based on the knowledge graph.
    """
    try:
        response = service.answer_query(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Document Intelligence API"}