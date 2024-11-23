import asyncio
import pytest
from ..digitalarchitects.core.websocketManager import WebSocketClientManager
from ..digitalarchitects.core.MainArchitecture import DigitalArchitect

class TestConnection:
    """Test Python-Unity connection and messaging"""
    
    @pytest.fixture
    async def setup_connection(self):
        ws_manager = WebSocketClientManager(
            uri="ws://localhost:8080/unity",
            api_key="test_key",
            autonomous_mode=False
        )
        await ws_manager.connect()
        return ws_manager
    
    async def test_basic_connection(self, setup_connection):
        """Test basic websocket connection"""
        ws_manager = setup_connection
        assert ws_manager.is_connected.is_set()
        
        # Test ping
        response = await ws_manager.send_command({
            "action": "ping",
            "message": "test"
        })
        assert response["status"] == "success"

    async def test_agent_communication(self, setup_connection):
        """Test agent-unity communication"""
        architect = DigitalArchitect(
            websocket_uri="ws://localhost:8080/unity",
            api_key="test_key"
        )
        await architect.start()
        
        # Test basic command
        response = await architect.handle_request(
            "Create a cube at position (0,0,0)",
            {"environment": "test_env"}
        )
        assert response["status"] == "success"