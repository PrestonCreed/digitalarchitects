from typing import Any, Callable, Dict, Optional
import logging
import traceback
from functools import wraps
import asyncio

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def handle_websocket_errors(func):
        """Decorator for handling WebSocket-related errors"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ConnectionError as e:
                logging.error(f"WebSocket connection error: {e}")
                return {"status": "error", "message": "Connection failed", "error": str(e)}
            except Exception as e:
                logging.error(f"WebSocket error: {e}\n{traceback.format_exc()}")
                return {"status": "error", "message": "Internal error", "error": str(e)}
        return wrapper

    @staticmethod
    def handle_llm_errors(func):
        """Decorator for handling LLM-related errors"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logging.error(f"LLM error: {e}\n{traceback.format_exc()}")
                return {
                    "status": "error",
                    "message": "LLM processing failed",
                    "error": str(e)
                }
        return wrapper

    @staticmethod
    def handle_environment_errors(func):
        """Decorator for handling environment-related errors"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Environment error: {e}\n{traceback.format_exc()}")
                return {
                    "status": "error",
                    "message": "Environment operation failed",
                    "error": str(e)
                }
        return wrapper

class MessageValidator:
    """Validates messages between Python and Unity"""
    
    @staticmethod
    def validate_unity_message(message: Dict[str, Any]) -> bool:
        """Validate incoming Unity messages"""
        required_fields = ['type', 'data']
        return all(field in message for field in required_fields)

    @staticmethod
    def validate_command(command: Dict[str, Any]) -> bool:
        """Validate outgoing commands to Unity"""
        required_fields = ['action', 'parameters']
        return all(field in command for field in required_fields)

    @staticmethod
    def validate_response(response: Dict[str, Any]) -> bool:
        """Validate responses"""
        required_fields = ['status']
        return all(field in response for field in required_fields)