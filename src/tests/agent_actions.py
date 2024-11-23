import asyncio
import pytest
from ..digitalarchitects.core.websocketManager import WebSocketClientManager
from ..digitalarchitects.core.MainArchitecture import DigitalArchitect

class TestAgentActions:
    """Test agent actions in Unity environment"""
    
    @pytest.fixture
    async def setup_agent(self):
        architect = DigitalArchitect(
            websocket_uri="ws://localhost:8080/unity",
            api_key="test_key"
        )
        await architect.start()
        return architect
    
    async def test_model_placement(self, setup_agent):
        """Test agent placing models in Unity"""
        architect = setup_agent
        response = await architect.handle_request(
            "Place a cube at coordinates (1,1,1)",
            {"environment": "test_env"}
        )
        assert "placement_id" in response.get("data", {})

    async def test_environment_analysis(self, setup_agent):
        """Test agent analyzing Unity environment"""
        architect = setup_agent
        response = await architect.handle_request(
            "Analyze the current scene",
            {"environment": "test_env"}
        )
        assert "internal_map" in response.get("data", {})