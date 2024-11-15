from typing import Dict, Any, List, Optional
import logging
from ..utils.LLMSystem import MessageHandler, LLMResponse
from dataclasses import dataclass
from ..utils.logging_config import LoggerMixin
from ..middleware.error_handler import ErrorHandler
from ..config.config_manager import LLMConfig

@dataclass
class ConversationState:
    """Tracks the current conversation context"""
    current_process: Optional[Dict[str, Any]] = None
    last_request: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = None
    project_context: Dict[str, Any] = None

class ConversationHandler:
    """Handles all LLM interactions and conversation management"""
    
    def __init__(self, message_handler: MessageHandler):
        self.llm = message_handler
        self.logger = logging.getLogger(__name__)
        self.state = ConversationState(conversation_history=[])
        
        # Load system prompts
        self.system_prompts = self._load_system_prompts()

    @ErrorHandler.handle_llm_errors
    async def process_request(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.state.last_request = message
            self.state.project_context = context
            self.state.conversation_history.append({
                "role": "user",
                "content": message
            })

            prompt = self._generate_contextual_prompt(message, context)
            response = await self.llm.process_message(
                prompt,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens
            )
            
            # Rest of the implementation...
            
        except Exception as e:
            self.logger.error(f"Error processing conversation: {e}")
            raise    

    async def process_request(self, message: str, context: Dict[str, Any]) -> LLMResponse:
        """Process a user request with full context"""
        try:
            # Update conversation state
            self.state.last_request = message
            self.state.project_context = context
            self.state.conversation_history.append({
                "role": "user",
                "content": message
            })

            # Generate full context prompt
            prompt = self._generate_contextual_prompt(message, context)
            
            # Get LLM response
            response = await self.llm.process_message(prompt)
            
            # Update conversation history
            if response.is_valid:
                self.state.conversation_history.append({
                    "role": "assistant",
                    "content": response.analysis
                })
            
            return response

        except Exception as e:
            self.logger.error(f"Error processing conversation: {str(e)}")
            raise

    def _generate_contextual_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Generate a complete prompt with all necessary context"""
        
        base_prompt = self.system_prompts["base_role"]
        
        return f"""{base_prompt}

Current Project Context:
{self._format_project_context(context)}

Conversation History:
{self._format_conversation_history()}

Current Request: {message}

Analyze this request and provide:
1. Complete understanding of what needs to be done
2. Any details you can confidently infer from context
3. Confidence levels in your understanding
4. Required tools and processes
5. Potential risks or impacts

If you are very confident (>90%) in your understanding and the task is low-impact, proceed with inferred details.
Only request clarification if:
- This is a major architectural decision
- You have low confidence in critical details
- The impact on the project is significant

Respond in a structured format that can be parsed for task execution."""

    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts for different conversation scenarios"""
        return {
            "base_role": """You are a Digital Architect agent responsible for creating and managing 3D environments. You have access to various tools for model generation, placement, and scene management. You should:
                          1. Work autonomously when confident
                          2. Consider project context in all decisions
                          3. Only ask for clarification when truly necessary
                          4. Maintain consistency with existing architecture""",
            
            "clarification": """When asking for clarification:
                              1. Be specific about what you need
                              2. Explain briefly why it's important
                              3. Provide any relevant context
                              4. Suggest possible options if applicable""",
            
            "task_completion": """When reporting task completion:
                                1. Be concise but informative
                                2. Highlight any important changes
                                3. Note any potential follow-up needs
                                4. Provide relevant details about results"""
        }

    def _format_project_context(self, context: Dict[str, Any]) -> str:
        """Format project context for prompt"""
        formatted = []
        for key, value in context.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)

    def _format_conversation_history(self) -> str:
        """Format relevant conversation history"""
        # Only include recent and relevant history
        relevant_history = self.state.conversation_history[-5:]  # Last 5 messages
        formatted = []
        for msg in relevant_history:
            formatted.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(formatted)

    async def generate_clarification_request(self, understanding: Dict[str, Any]) -> str:
        """Generate a natural clarification request"""
        prompt = f"""{self.system_prompts['clarification']}

Understanding: {understanding}

Generate a clear, concise question to get the critical information needed.
Focus only on what's most important."""

        response = await self.llm.process_message(prompt)
        return response.analysis

    async def generate_completion_message(self, result: Dict[str, Any]) -> str:
        """Generate a completion message"""
        prompt = f"""{self.system_prompts['task_completion']}

Task Result: {result}

Generate a concise completion message highlighting the key outcomes."""

        response = await self.llm.process_message(prompt)
        return response.analysis