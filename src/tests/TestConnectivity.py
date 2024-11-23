import pytest
import asyncio
from ..digitalarchitects.core.websocketManager import WebSocketClientManager
from ..digitalarchitects.core.MainArchitecture import DigitalArchitect
from ..digitalarchitects.utils.LLMSystem import MessageHandler
from ..digitalarchitects.config.config_manager import ConfigManager

class TestConnectivity:
    """Tests all connection-related functionality"""
    
    @pytest.fixture
    async def setup_components(self):
        config = ConfigManager()
        ws_manager = WebSocketClientManager(
            uri="ws://localhost:8080/unity",
            api_key="test_key"
        )
        llm_handler = MessageHandler(config.get_llm_config())
        architect = DigitalArchitect(ws_manager)
        return ws_manager, llm_handler, architect

    async def test_unity_connection(self, setup_components):
        """Test basic connection to Unity"""
        ws_manager, _, _ = setup_components
        await ws_manager.connect()
        assert ws_manager.is_connected.is_set()
        
        # Test basic message
        response = await ws_manager.send_command({
            "action": "ping",
            "parameters": {}
        })
        assert response["status"] == "success"

    async def test_llm_connection(self, setup_components):
        """Test LLM connectivity"""
        _, llm_handler, _ = setup_components
        response = await llm_handler.process_message("Test message")
        assert response is not None
        assert response.is_valid