"""
Celery background tasks for document processing.

This file defines the Celery tasks that run in the background:
1. process_document_task: Main task for processing uploaded documents
   - Takes a file path and original filename
   - Uses DocumentProcessor to parse and ingest the document
   - Cleans up temporary files after processing
   - Handles errors gracefully with proper cleanup

The task uses the @celery.task(bind=True) decorator to enable:
- Self-referencing for task metadata
- Proper error handling and logging
- Task state management
"""

import os
from celery_app import celery
from processing_service import DocumentProcessor

@celery.task(bind=True)
def process_document_task(self, file_path: str, original_filename: str):
    """
    Celery task to process a document in the background.
    It uses the DocumentProcessor service to perform the actual work.
    """
    try:
        processor = DocumentProcessor(file_path, original_filename)
        result = processor.process()
        # Clean up the temporary file after processing
        os.remove(file_path)
        return {"status": "SUCCESS", "result": result}
    except Exception as e:
        # Clean up the temporary file even if an error occurs
        if os.path.exists(file_path):
            os.remove(file_path)
        # Log the error and re-raise to mark the task as FAILED
        print(f"Task failed for file {original_filename}: {e}")
        # You can add more robust error handling/logging here
        raise