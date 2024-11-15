# as an example of how a tool can use websockets to communicate with the unity environment, this is the tool for importing models


from typing import Any, Dict
import asyncio
from ..base_tool import Tool
from ...core.websocketManager import WebSocketClientManager
import os

# Initialize WebSocketClientManager with Unity server URI and API key
unity_ws_uri = "ws://localhost:8080/unity"
unity_api_key = os.getenv("UNITY_API_KEY", "SuperSecretKey123")  # Replace with secure key management

ws_manager = WebSocketClientManager(unity_ws_uri, unity_api_key)

async def import_model(model_path: str) -> Dict[str, Any]:
    """
    Sends a command to Unity to import a 3D model.
    """
    command = {
        "action": "import_model",
        "model_path": model_path
    }
    
    # Ensure connection is established
    if not ws_manager.connection:
        await ws_manager.connect()
    
    response = await ws_manager.send_command(command)
    return response

import_model_tool = Tool(
    name="ImportModelTool",
    supported_tasks=["import_model"],
    execute=lambda model_path: asyncio.run(import_model(model_path)),
    requirements={"software": "Unity2023"}  # Update as needed
)