import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, name: str, log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Default log file if not provided
        if not log_file:
            log_file = f"logs/{name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        self.logger.exception(message, extra=kwargs)

# Create logger instances for different modules
api_logger = Logger("api")
task_logger = Logger("tasks")
db_logger = Logger("database")
qdrant_logger = Logger("qdrant")
openai_logger = Logger("openai")
redis_logger = Logger("redis")
