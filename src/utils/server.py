import zmq
import asyncio
import json
import logging
from typing import Dict, Any
from dataclasses import asdict
from LLMSystem import MessageHandler, ArchitectRequest

class DigitalArchitectServer:
    def __init__(self, port: int = 5555):
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        
        # Initialize core components
        self.architect = DigitalArchitect()
        self.conversation_handler = ConversationHandler(MessageHandler())
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    async def start(self):
        """Start the server and listen for requests"""
        self.socket.bind(f"tcp://*:{self.port}")
        self.logger.info(f"Digital Architect Server started on port {self.port}")
        
        while True:
            try:
                # Receive message from Unity
                message_data = await self.receive_message()
                self.logger.info(f"Received request: {message_data}")
                
                # Extract project context if provided
                project_context = message_data.get('metadata', {}).get('project_context', {})
                
                # Process with LLM
                response = await self.message_handler.process_message(
                    message_data['message'],
                    project_context
                )
                
                # Send response back to Unity
                await self.send_response(response)
                
            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                await self.send_error(str(e))

    async def receive_message(self) -> Dict[str, Any]:
        """Receive and parse message from Unity"""
        message = self.socket.recv_string()
        return json.loads(message)
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message from Unity"""
        try:
            # Extract message and context
            message = message_data['message']
            project_context = message_data.get('metadata', {}).get('project_context', {})
            
            # Process through conversation handler
            conversation_response = await self.conversation_handler.process_request(
                message, 
                project_context
            )
            
            if conversation_response.is_valid:
                # Process through architect
                architect_response = await self.architect.handle_request(
                    message,
                    project_context
                )
                
                # Only return if we need user input or task is complete
                if architect_response.get("needs_clarification"):
                    return {
                        "type": "clarification",
                        "message": await self.conversation_handler.generate_clarification_request(
                            architect_response
                        )
                    }
                elif architect_response.get("is_complete"):
                    return {
                        "type": "completion",
                        "message": await self.conversation_handler.generate_completion_message(
                            architect_response
                        )
                    }
                else:
                    return {"type": "processing"}
            
            return {"type": "error", "message": "Invalid request"}
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {"type": "error", "message": str(e)}

    async def send_response(self, response: ArchitectRequest):
        """Send response back to Unity"""
        response_json = json.dumps(asdict(response))
        self.socket.send_string(response_json)

    async def send_error(self, error_message: str):
        """Send error response to Unity"""
        error_response = json.dumps({
            'is_valid': False,
            'error_message': error_message,
            'analysis': '',
            'building_info': {}
        })
        self.socket.send_string(error_response)

    def cleanup(self):
        """Cleanup resources"""
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    server = DigitalArchitectServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.cleanup()