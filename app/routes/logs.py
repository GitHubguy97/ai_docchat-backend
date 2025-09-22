from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.utils.logger import api_logger
import json
from datetime import datetime

router = APIRouter()

class LogEntry(BaseModel):
    timestamp: str
    level: str
    name: str
    message: str
    data: Dict[str, Any]
    userAgent: Optional[str] = None
    url: Optional[str] = None

@router.post("/logs")
def receive_frontend_log(log_entry: LogEntry):
    """
    Receive and log frontend errors and warnings.
    """
    try:
        # Log to backend logger with frontend context
        log_message = f"[Frontend {log_entry.name}] {log_entry.message}"
        
        if log_entry.level == 'error':
            api_logger.error(log_message, 
                           frontend_data=log_entry.data,
                           user_agent=log_entry.userAgent,
                           url=log_entry.url,
                           timestamp=log_entry.timestamp)
        elif log_entry.level == 'warn':
            api_logger.warning(log_message,
                             frontend_data=log_entry.data,
                             user_agent=log_entry.userAgent,
                             url=log_entry.url,
                             timestamp=log_entry.timestamp)
        else:
            api_logger.info(log_message,
                          frontend_data=log_entry.data,
                          user_agent=log_entry.userAgent,
                          url=log_entry.url,
                          timestamp=log_entry.timestamp)
        
        return {"status": "logged"}
        
    except Exception as e:
        api_logger.exception(f"Failed to log frontend entry", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log entry"
        )
