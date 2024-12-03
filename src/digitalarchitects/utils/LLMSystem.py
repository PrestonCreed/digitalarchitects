from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import yaml
import json
import os
import logging
import asyncio
import aiohttp
import time
from huggingface import transformers
import pytorch

# Model Types and Configuration
class LLMType(str, Enum):
    GPT4 = "gpt-4o"
    GPT4O = "gpt-4o-mini"
    O1 = "o1-mini"
    LLAMA31 = "llama-3.1"
    QWEN25_CODER = "qwen-2.5-coder"
    CLAUDE35_SONNET = "claude-3.5-sonnet"
    CLAUDE35_SONNET_NEW = "claude-3.5-sonnet-new"
    GEMINI_PRO15 = "gemini-pro-1.5"
    HERMES3_FORGE = "hermes-3-forge"

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
    local_path: Optional[str] = None  # For local models like Llama
    
    @classmethod
    def load(cls, config_path: str = "config/llm_config.yaml") -> 'LLMConfig':
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                return cls(
                    selected_model=LLMType(config_data['selected_model']),
                    api_keys=ApiKeys(**config_data['api_keys']),
                    enabled_models={LLMType(k): v for k, v in config_data['enabled_models'].items()},
                    local_path=config_data.get('local_path')
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
            },
            local_path="path/to/llama/model"
        )

@dataclass
class ArchitectRequest:
    """Stores the processed analysis from the LLM"""
    analysis: str  # Full text analysis
    building_info: Dict[str, Any]  # Extracted key information
    is_valid: bool = True
    error_message: Optional[str] = None

@dataclass
class LLMResponse:
    """Raw LLM response and additional processing"""
    analysis: str  # Full analysis text
    extracted_info: Dict[str, Any]  # Structured data
    raw_response: Dict[str, Any]  # Full LLM response
    model_used: str
    token_usage: Dict[str, int]
    latency: float

class LLMService(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = None

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
        return f"""
Current Project Context:
- World Theme: {context.get('theme', 'Not specified')}
- Time Period: {context.get('time_period', 'Not specified')}
- Existing Buildings: {context.get('existing_buildings', 'None specified')}
- Environmental Conditions: {context.get('environment', 'Not specified')}
- Special Requirements: {context.get('special_requirements', 'None specified')}
"""

    @abstractmethod
    async def process_request(self, message: str, project_context: Optional[Dict] = None) -> LLMResponse:
        pass

class GPTService(LLMService):
    async def process_request(self, message: str, project_context: Optional[Dict] = None) -> LLMResponse:
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.config.api_keys.openai}"}
            )
        
        start_time = time.time()
        
        try:
            prompt = await self.format_prompt(message, project_context)
            payload = {
                "model": self.config.selected_model.value,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2048,
                "n": 1,
                "stop": None
            }
            
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                timeout=60  # Adjust timeout as needed
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"OpenAI API Error: {error_text}")
                    raise Exception(f"OpenAI API returned status code {response.status}")
                
                result = await response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            # Parse structured info (example implementation)
            extracted_info = self.parse_response(content)
            
            return LLMResponse(
                analysis=content,
                extracted_info=extracted_info,
                raw_response=result,
                model_used=self.config.selected_model.value,
                token_usage=result.get("usage", {}),
                latency=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request with GPT: {str(e)}")
            raise

    def parse_response(self, content: str) -> Dict[str, Any]:
        # Implement parsing logic to extract structured information
        # This is a placeholder for actual parsing code
        return {
            "building_type": "parsed_type",
            "requirements": [],
            "location_data": {}
        }

class AnthropicService(LLMService):
    async def process_request(self, message: str, project_context: Optional[Dict] = None) -> LLMResponse:
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "x-api-key": self.config.api_keys.anthropic,
                    "Content-Type": "application/json"
                }
            )
                
        start_time = time.time()
        
        try:
            prompt = await self.format_prompt(message, project_context)
            payload = {
                "model": self.config.selected_model.value,
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 2048,
                "temperature": 0.7,
                "stop_sequences": ["\n\nHuman:"]
            }
            
            async with self.session.post(
                "https://api.anthropic.com/v1/complete",
                json=payload,
                timeout=60  # Adjust timeout as needed
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Anthropic API Error: {error_text}")
                    raise Exception(f"Anthropic API returned status code {response.status}")
                
                result = await response.json()
            
            content = result["completion"]
            
            # Parse structured info
            extracted_info = self.parse_response(content)
            
            return LLMResponse(
                analysis=content,
                extracted_info=extracted_info,
                raw_response=result,
                model_used=self.config.selected_model.value,
                token_usage={"total_tokens": result.get("completion_tokens", 0)},
                latency=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request with Anthropic: {str(e)}")
            raise

    def parse_response(self, content: str) -> Dict[str, Any]:
        # Implement parsing logic to extract structured information
        # This is a placeholder for actual parsing code
        return {
            "building_type": "parsed_type",
            "requirements": [],
            "location_data": {}
        }

class LlamaService(LLMService):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.model = self._load_llama_model()

    def _load_llama_model(self):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.local_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.config.local_path)
            self.model.eval()
            if torch.cuda.is_available():
                self.model.to('cuda')
            return self.model
        except Exception as e:
            self.logger.error(f"Error loading Llama model: {str(e)}")
            raise

    async def process_request(self, message: str, project_context: Optional[Dict] = None) -> LLMResponse:
        start_time = time.time()
        
        try:
            prompt = await self.format_prompt(message, project_context)
            inputs = self.tokenizer.encode(prompt, return_tensors='pt')
            if torch.cuda.is_available():
                inputs = inputs.to('cuda')
            outputs = self.model.generate(inputs, max_length=2048)
            content = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse structured info
            extracted_info = self.parse_response(content)
            
            return LLMResponse(
                analysis=content,
                extracted_info=extracted_info,
                raw_response={},  # Local model may not have raw response
                model_used=self.config.selected_model.value,
                token_usage={"prompt_tokens": len(inputs[0]), "completion_tokens": len(outputs[0])},
                latency=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request with Llama: {str(e)}")
            raise

    def parse_response(self, content: str) -> Dict[str, Any]:
        # Implement parsing logic to extract structured information
        # This is a placeholder for actual parsing code
        return {
            "building_type": "parsed_type",
            "requirements": [],
            "location_data": {}
        }

class MessageHandler:
    def __init__(self, config_path: str = "config/llm_config.yaml"):
        self.config = LLMConfig.load(config_path)
        self.llm_service = self._create_llm_service()
        self.logger = logging.getLogger(__name__)

    def _create_llm_service(self) -> LLMService:
        if self.config.selected_model in [LLMType.GPT4, LLMType.GPT4O, LLMType.O1]:
            return GPTService(self.config)
        elif self.config.selected_model in [LLMType.CLAUDE35_SONNET, LLMType.CLAUDE35_SONNET_NEW]:
            return AnthropicService(self.config)
        elif self.config.selected_model == LLMType.LLAMA31:
            return LlamaService(self.config)
        else:
            raise ValueError(f"Unsupported model type: {self.config.selected_model}")

    async def process_message(self, message: str, project_context: Optional[Dict] = None) -> ArchitectRequest:
        try:
            llm_response = await self.llm_service.process_request(message, project_context)
            return ArchitectRequest(
                analysis=llm_response.analysis,
                building_info=llm_response.extracted_info,
                is_valid=True
            )
        except Exception as e:
            self.logger.error(f"Failed to process message: {str(e)}")
            return ArchitectRequest(
                analysis="",
                building_info={},
                is_valid=False,
                error_message=str(e)
            )
