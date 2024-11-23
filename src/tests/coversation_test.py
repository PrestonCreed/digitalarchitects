class TestConversation:
    """Test conversation capabilities"""
    
    async def test_basic_conversation(self, setup_agent):
        """Test basic conversation flow"""
        architect = setup_agent
        response = await architect.handle_request(
            "Hello, what can you help me with?",
            {"environment": "test_env"}
        )
        assert response.get("message") is not None

    async def test_context_memory(self, setup_agent):
        """Test agent memory and context retention"""
        architect = setup_agent
        
        # First message
        response1 = await architect.handle_request(
            "Create a red cube",
            {"environment": "test_env"}
        )
        
        # Follow-up referring to previous
        response2 = await architect.handle_request(
            "Make it bigger",
            {"environment": "test_env"}
        )
        
        assert response2.get("status") == "success"