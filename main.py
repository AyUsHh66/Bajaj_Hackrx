"""
Main FastAPI application for the HackRx Document Intelligence API.

This file serves as the main entry point for the FastAPI application. It provides:
1. API authentication using Bearer tokens
2. A main endpoint (/hackrx/run) that processes questions about documents
3. Document ingestion and question answering using existing vector database data
4. Integration with Celery for background processing (though currently bypassed)

The application uses a retrieval service to answer questions from pre-processed 
documents stored in a Neo4j vector database.
"""

# main.py

import os
import time
import requests
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from celery.result import AsyncResult
from pathlib import Path

from models import HackRxRequest, HackRxResponse
from tasks import process_document_task
from retrieval_service import RetrievalService
# --- 1. Import the graph object to check for existing documents ---
from database import graph

# --- Configuration ---
# In a real application, this would come from a secure source, not hardcoded.
API_KEY = "Rachu" 

# Create a directory for temporary file downloads
DOWNLOAD_DIR = Path("temp_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Document Intelligence API for HackRx",
    description="Processes a document and answers questions about it.",
)

# --- Authentication ---
security = HTTPBearer()

def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validates the API key from the Authorization header."""
    if credentials.scheme != "Bearer" or credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )
    return credentials.credentials

# --- Main Endpoint ---
@app.post("/hackrx/run", response_model=HackRxResponse)
def run_pipeline(
    request: HackRxRequest,
    api_key: str = Depends(get_api_key)
):
    """
    This endpoint answers a list of questions based on the existing data
    in the vector database, ignoring the 'documents' key in the request.
    """
    try:
        print("Bypassing ingestion. Answering questions from existing VectorDB data.")
        
        # --- Answer questions using the existing data ---
        retrieval_service = RetrievalService()
        answers = []
        for question in request.questions:
            print(f"Answering question: {question}")
            answer_data = retrieval_service.answer_query(question)
            answers.append(answer_data["answer"])
            
        return HackRxResponse(answers=answers)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the HackRx Document Intelligence API"}
