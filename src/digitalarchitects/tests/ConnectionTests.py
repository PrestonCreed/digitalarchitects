import unittest
import asyncio
import pytest
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project-specific imports
from ..config.ConfigManager import ConfigManager
from ..utils.LLMSystem import MessageHandler
from ..instances.InstanceManager import InstanceManager
from ..core.websocketManager import WebSocketClientManager
from ..tools.tool_registry import Tool
from ..core.tool_manager import ArchitectToolManager
from ..memory.MemorySystem import (
    MemoryManager,
    CollectiveMemory,
    ConversationMemory,
    ActionMemory,
    KnowledgeMemory
)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Core system tests
class TestDigitalArchitectsCore:
    """Test core system initialization and basic functionality"""
    
    async def setup_async(self):
        """Setup test environment"""
        self.config = ConfigManager()
        self.llm_handler = MessageHandler()
        self.instance_manager = InstanceManager(self.config, "test_project")
        
    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test complete system initialization sequence"""
        try:
            # Test config loading
            assert self.config is not None
            assert self.config.get_llm_config() is not None
            
            # Test LLM system
            assert self.llm_handler is not None
            llm_response = await self.llm_handler.process_message("test message")
            assert llm_response is not None
            
            # Test instance management
            instance_id = await self.instance_manager.create_instance(
                name="test_architect",
                primary_objective="test objective"
            )
            assert instance_id is not None
            
            # Verify instance created
            instance = self.instance_manager.instances.get(instance_id)
            assert instance is not None
            assert instance.status == "active"
            
        except Exception as e:
            pytest.fail(f"System initialization failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection and basic message passing"""
        ws_manager = WebSocketClientManager("ws://localhost:8080", "test_key")
        
        try:
            # Test connection
            await ws_manager.connect()
            assert ws_manager.is_connected.is_set()
            
            # Test message sending
            test_message = {"type": "test", "content": "hello"}
            response = await ws_manager.send_command(test_message)
            assert response is not None
            
            # Test disconnection
            await ws_manager.disconnect()
            assert not ws_manager.is_connected.is_set()
            
        except Exception as e:
            pytest.fail(f"WebSocket test failed: {str(e)}")

class TestToolSystem:
    """Test tool registration and execution"""
    
    async def setup_async(self):
        self.tool_manager = ArchitectToolManager()
        
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test tool registration process"""
        # Register test tool
        test_tool = Tool(
            name="test_tool",
            action_type="test",
            requirements=["test_req"]
        )
        
        try:
            self.tool_manager.registry.register_tool(test_tool)
            
            # Verify registration
            registered_tools = self.tool_manager.registry.list_all_tools()
            assert "test_tool" in registered_tools
            
            # Test tool retrieval
            tools = self.tool_manager.registry.get_tools_for_task("test")
            assert len(tools) > 0
            assert tools[0].name == "test_tool"
            
        except Exception as e:
            pytest.fail(f"Tool registration test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution pipeline"""
        try:
            # Prepare test context
            context = {
                "test_req": "test_value",
                "inferred_details": {}
            }
            
            # Execute tool
            result = await self.tool_manager.execute_tool_chain(
                "test",
                context
            )
            
            assert result is not None
            assert "test_tool" in result
            assert result["test_tool"]["success"]
            
        except Exception as e:
            pytest.fail(f"Tool execution test failed: {str(e)}")

class TestMemorySystem:
    """Test memory operations"""
    
    async def setup_async(self):
        self.memory_manager = MemoryManager("test_architect")
        self.collective_memory = CollectiveMemory("test_project")
        
    @pytest.mark.asyncio
    async def test_memory_operations(self):
        """Test basic memory operations"""
        try:
            # Test memory addition
            test_memory = ConversationMemory(
                timestamp=datetime.datetime.now().timestamp(),
                content={"message": "test"},
                role="user",
                message="test message"
            )
            
            self.memory_manager.add_memory(test_memory)
            
            # Test memory retrieval
            memories = self.memory_manager.query_memories(
                tags={"conversation"},
                limit=1
            )
            
            assert len(memories) > 0
            assert memories[0].content["message"] == "test"
            
            # Test collective memory
            await self.collective_memory.add_collective_knowledge(
                category="test",
                content={"data": "test"},
                contributor_id="test_architect"
            )
            
            roles = self.collective_memory.get_architect_roles()
            assert len(roles) > 0
            
        except Exception as e:
            pytest.fail(f"Memory system test failed: {str(e)}")

# Run tests
if __name__ == '__main__':
    pytest.main([__file__])