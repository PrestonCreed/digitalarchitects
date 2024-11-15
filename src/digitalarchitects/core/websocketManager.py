import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional  # Added missing imports
from ..utils.logging_config import LoggerMixin
from ..middleware.error_handler import ErrorHandler, MessageValidator
from ..config.ConfigManager import WebSocketConfig

class WebSocketClientManager:
    """Manages the WebSocket connection to Unity."""
    
    def __init__(self, uri: str, api_key: str, autonomous_mode: bool = False):  # Added default value
        self.uri = uri
        self.api_key = api_key
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self.message_queue = asyncio.Queue()
        self.reconnect_interval = 5
        self.is_connected = asyncio.Event()
        self.autonomous_mode = autonomous_mode  # Now properly defined
        self.action_queue = asyncio.Queue()

    @ErrorHandler.handle_websocket_errors
    async def connect(self):
        try:
            self.connection = await websockets.connect(
                self.config.uri,
                extra_headers={"X-API-KEY": self.config.api_key}
            )
            self.logger.info(f"Connected to Unity WebSocket server at {self.config.uri}")
            self.is_connected.set()
        except Exception as e:
            self.logger.error(f"Failed to connect to Unity WebSocket server: {e}")
            self.is_connected.clear()
            raise

    @ErrorHandler.handle_websocket_errors
    async def send_command(self, command: dict) -> dict:
        if not MessageValidator.validate_command(command):
            self.logger.error(f"Invalid command format: {command}")
            return {"status": "error", "message": "Invalid command format"}
            
        try:
            if not self.connection:
                await self.connect()
            
            message = json.dumps(command)
            await self.connection.send(message)
            self.logger.debug(f"Sent command: {message}")
            
            response = await self.connection.recv()
            self.logger.debug(f"Received response: {response}")
            
            parsed_response = json.loads(response)
            if not MessageValidator.validate_response(parsed_response):
                raise ValueError("Invalid response format from Unity")
                
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
            return {"status": "failure", "error": str(e)}    
    
    async def connect(self):
        try:
            self.connection = await websockets.connect(
                self.uri,
                extra_headers={"X-API-KEY": self.api_key}
            )
            self.logger.info(f"Connected to Unity WebSocket server at {self.uri}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Unity WebSocket server: {e}")

    async def start(self):
        """Start manager with connection monitoring"""
        asyncio.create_task(self._connection_monitor())
        asyncio.create_task(self._process_message_queue())

    async def start(self):
        await self.connect()
        if self.autonomous_mode:
            asyncio.create_task(self._autonomous_action_processor())
        
    
    async def _connection_monitor(self):
        """Monitor and maintain connection"""
        while True:
            try:
                if not self.connection:
                    await self.connect()
                    if self.connection:
                        self.is_connected.set()
                await asyncio.sleep(self.reconnect_interval)
            except Exception as e:
                self.logger.error(f"Connection monitor error: {e}")
                self.is_connected.clear()
                
    async def _process_message_queue(self):
        """Process queued messages when connection is available"""
        while True:
            message = await self.message_queue.get()
            await self.is_connected.wait()  # Wait for connection
            try:
                await self._send_message(message)
            except Exception as e:
                self.logger.error(f"Failed to send queued message: {e}")
                await self.message_queue.put(message)  # Re-queue failed messages
            self.message_queue.task_done()        
    
    async def send_command(self, command: dict) -> dict:
        try:
            if not self.connection:
                await self.connect()
            message = json.dumps(command)
            await self.connection.send(message)
            self.logger.debug(f"Sent command: {message}")
            
            # Wait for response
            response = await self.connection.recv()
            self.logger.debug(f"Received response: {response}")
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
            return {"status": "failure", "error": str(e)}
        
    async def _autonomous_action_processor(self):
        """Process actions autonomously without user confirmation"""
        while True:
            try:
                action = await self.action_queue.get()
                if not self._requires_user_approval(action):
                    await self.send_command(action)
                else:
                    self.logger.warning(f"Action {action['type']} requires user approval despite autonomous mode")
                    # Handle critical actions that always need approval
                await asyncio.sleep(0.1)  # Prevent overwhelming the system
            except Exception as e:
                self.logger.error(f"Error in autonomous processing: {e}")

    def _requires_user_approval(self, action: Dict[str, Any]) -> bool:
        """Check if action requires user approval even in autonomous mode"""
        CRITICAL_ACTIONS = ['delete_environment', 'reset_scene', 'modify_core_settings']
        return action.get('type') in CRITICAL_ACTIONS                
    
    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            self.logger.info("Disconnected from Unity WebSocket server.")