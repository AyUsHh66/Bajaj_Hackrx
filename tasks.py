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