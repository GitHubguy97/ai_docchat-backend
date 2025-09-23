from fastapi import APIRouter, HTTPException, status, Depends
from app.redis_client import redis_client
from app.models.models import Document
from app.dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a document processing job.
    
    Args:
        job_id: The job ID (document ID)
        
    Returns:
        Job status with progress information
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == int(job_id)).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get job status from Redis
        job_key = f"job:{job_id}"
        job_data = redis_client.get(job_key)
        
        if job_data:
            import json
            job_info = json.loads(job_data)
            status_info = job_info.get('status', 'unknown')
            progress = job_info.get('progress', 0)
        else:
            # Fallback to document status
            status_info = document.status
            progress = 100 if document.status == 'completed' else 0
        
        return {
            "job_id": job_id,
            "document_id": document.id,
            "title": document.title,
            "status": status_info,
            "progress": progress,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job status: {str(e)}"
        )
