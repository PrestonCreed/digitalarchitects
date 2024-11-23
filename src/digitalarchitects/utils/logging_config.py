import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

class LoggingManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_manager=None):
        if not hasattr(self, '_initialized'):
            self.config = config_manager
            self.setup_logging()
            self._initialized = True

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(__file__).parent.parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "digitalarchitects.log"
        
        # Get log level from config or default to INFO
        log_level = (self.config.config.get("logging", {}).get("level", "INFO")
                    if self.config else "INFO")

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Setup handlers
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Remove any existing handlers
        root_logger.handlers = []
        
        # Add our handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        return logging.getLogger(name)

class LoggerMixin:
    """Mixin to add logging capabilities to classes"""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = LoggingManager.get_logger(self.__class__.__name__)
        return self._logger