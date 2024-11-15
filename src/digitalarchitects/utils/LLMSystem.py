from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import yaml
import json
import os
from abc import ABC, abstractmethod
import logging
import asyncio

# LLM Types and Configuration
class LLMType(str, Enum):
    GPT4 = "gpt4"
    GPT4O = "gpt4o"
    O1 = "o1"
    LLAMA31 = "llama31"
    CLAUDE35_SONNET = "claude35_sonnet"
    CLAUDE35_SONNET_NEW = "claude35_sonnet_new"
    QWEN25_CODER = "qwen25_coder"
    HERMES3_FORGE = "hermes3_forge"
    GEMINI_PRO15 = "gemini_pro15"

@dataclass
class ApiKeys:
    openai: Optional[str] = None
    anthropic: Optional[str] = None
    google: Optional[str] = None

@dataclass
class LLMConfig:
    selected_model: LLMType
    api_keys: ApiKeys
    enabled_models: Dict[LLMType, bool]
    
    @classmethod
    def load(cls, config_path: str = "config/llm_config.yaml") -> 'LLMConfig':
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                return cls(
                    selected_model=LLMType(config_data['selected_model']),
                    api_keys=ApiKeys(**config_data['api_keys']),
                    enabled_models={LLMType(k): v for k, v in config_data['enabled_models'].items()}
                )
        except FileNotFoundError:
            return cls.create_default()
    
    def save(self, config_path: str = "config/llm_config.yaml"):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(asdict(self), f)
    
    @classmethod
    def create_default(cls) -> 'LLMConfig':
        return cls(
            selected_model=LLMType.LLAMA31,
            api_keys=ApiKeys(),
            enabled_models={
                LLMType.GPT4: False,
                LLMType.GPT4O: False,
                LLMType.O1: False,
                LLMType.LLAMA31: True
            }
        )

@dataclass
class ArchitectRequest:
    """Stores the processed analysis from the LLM"""
    analysis: str  # Full text analysis
    building_info: Dict[str, Any]  # Extracted key information if needed
    is_valid: bool = True
    error_message: Optional[str] = None

@dataclass
class LLMResponse:
    """Raw LLM response and additional processing"""
    analysis: str  # Full analysis text
    extracted_info: Dict[str, Any]  # Any structured data we need
    raw_response: Dict[str, Any]  # Full LLM response for reference

class LLMService(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    async def format_prompt(self, message: str, project_context: Optional[Dict] = None) -> str:
        """Format the message into a proper prompt for the LLM."""
        context_str = self._format_context(project_context) if project_context else ""
        
        return f"""As a Digital Architect agent, I assist in designing and building elements in simulated environments.

User Request: {message}

{context_str}

Please provide a detailed analysis including:

1. Architectural Analysis:
   - Style and design considerations
   - Material requirements
   - Structural needs

2. Placement Considerations:
   - Optimal location factors
   - Environmental integration
   - Access requirements

3. Required Elements:
   - Essential components
   - Interior/exterior features
   - Functional requirements

4. Construction Approach:
   - Building methodology
   - Material considerations
   - Construction sequence

5. Additional Considerations:
   - Historical accuracy
   - Functionality requirements
   - Integration with existing structures

Provide your analysis in natural language, thinking as an architect would.
"""

    def _format_context(self, context: Dict) -> str:
        """Format project context for the prompt"""
        return f"""
Current Project Context:
- World Theme: {context.get('theme', 'Not specified')}
- Time Period: {context.get('time_period', 'Not specified')}
- Existing Buildings: {context.get('existing_buildings', 'None specified')}
- Environmental Conditions: {context.get('environment', 'Not specified')}
- Special Requirements: {context.get('special_requirements', 'None specified')}
"""

# Specific LLM Implementations
class GPTService(LLMService):
    def __init__(self, config: LLMConfig, model_name: str):
        super().__init__(config)
        self.model_name = model_name
        self.api_key = config.api_keys.openai

    async def process_request(self, message: str) -> LLMResponse:
        try:
            import openai
            openai.api_key = self.api_key
            
            prompt = await self.format_prompt(message)
            response = await openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the response
            content = response.choices[0].message.content
            parsed_response = self._parse_gpt_response(content)
            
            return LLMResponse(
                building_type=parsed_response['building_type'],
                requirements=parsed_response['requirements'],
                context=parsed_response['context'],
                raw_response=response
            )
        except Exception as e:
            self.logger.error(f"Error processing request with GPT: {str(e)}")
            raise

class LlamaService(LLMService):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.model = self._load_llama_model()

    def _load_llama_model(self):
        # Implementation for loading local Llama model
        pass

    async def process_request(self, message: str) -> LLMResponse:
        try:
            prompt = await self.format_prompt(message)
            # Process with local Llama model
            response = "Not implemented"  # Replace with actual implementation
            return LLMResponse(
                building_type="test",
                requirements=[],
                context={},
                raw_response={}
            )
        except Exception as e:
            self.logger.error(f"Error processing request with Llama: {str(e)}")
            raise

# Main Message Handler
class MessageHandler:
    def __init__(self, config_path: str = "config/llm_config.yaml"):
        self.config = LLMConfig.load(config_path)
        self.llm_service = self._create_llm_service()
        self.logger = logging.getLogger(__name__)

    def _create_llm_service(self) -> LLMService:
        if self.config.selected_model in [LLMType.GPT4, LLMType.GPT4O, LLMType.O1]:
            return GPTService(self.config, str(self.config.selected_model))
        elif self.config.selected_model == LLMType.LLAMA31:
            return LlamaService(self.config)
        else:
            raise ValueError(f"Unsupported model type: {self.config.selected_model}")

    async def process_message(self, message: str) -> ArchitectRequest:
        try:
            llm_response = await self.llm_service.process_request(message)
            return ArchitectRequest(
                building_type=llm_response.building_type,
                requirements=llm_response.requirements,
                context=llm_response.context,
                is_valid=True
            )
        except Exception as e:
            self.logger.error(f"Failed to process message: {str(e)}")
            return ArchitectRequest(
                building_type="",
                requirements=[],
                context={},
                is_valid=False,
                error_message=str(e)
            )

# Usage Example
async def main():
    handler = MessageHandler()
    request = await handler.process_message(
        "I want a sheriff's office in the town, stacked with western objects"
    )
    print(f"Processed Request: {request}")

if __name__ == "__main__":
    asyncio.run(main())