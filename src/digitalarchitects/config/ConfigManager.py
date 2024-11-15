import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class LLMConfig:
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000

@dataclass
class WebSocketConfig:
    uri: str
    api_key: str
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0

@dataclass
class EnvironmentConfig:
    auto_connect: bool = True
    default_port: int = 8080
    environment_id: Optional[str] = None

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._get_default_config_path()
        self.config: Dict[str, Any] = {}
        self.load_config()

    def _get_default_config_path(self) -> str:
        """Get default config path based on environment"""
        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.yaml")

    def load_config(self):
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                self.logger.warning(f"Config file not found at {self.config_path}. Using defaults.")
                self.config = self._create_default_config()
                self.save_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.config = self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "llm": {
                "api_key": os.getenv("LLM_API_KEY", ""),
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "websocket": {
                "uri": "ws://localhost:8080/unity",
                "api_key": os.getenv("UNITY_WS_KEY", "default_key"),
                "retry_attempts": 3,
                "retry_delay": 1.0,
                "timeout": 30.0
            },
            "environment": {
                "auto_connect": True,
                "default_port": 8080,
                "environment_id": None
            },
            "logging": {
                "level": "INFO",
                "file": "digitalarchitects.log"
            }
        }

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration"""
        llm_config = self.config.get("llm", {})
        return LLMConfig(
            api_key=llm_config.get("api_key", ""),
            model=llm_config.get("model", "gpt-4"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 2000)
        )

    def get_websocket_config(self) -> WebSocketConfig:
        """Get WebSocket configuration"""
        ws_config = self.config.get("websocket", {})
        return WebSocketConfig(
            uri=ws_config.get("uri", "ws://localhost:8080/unity"),
            api_key=ws_config.get("api_key", "default_key"),
            retry_attempts=ws_config.get("retry_attempts", 3),
            retry_delay=ws_config.get("retry_delay", 1.0),
            timeout=ws_config.get("timeout", 30.0)
        )

    def get_environment_config(self) -> EnvironmentConfig:
        """Get environment configuration"""
        env_config = self.config.get("environment", {})
        return EnvironmentConfig(
            auto_connect=env_config.get("auto_connect", True),
            default_port=env_config.get("default_port", 8080),
            environment_id=env_config.get("environment_id")
        )

    def update_config(self, section: str, key: str, value: Any):
        """Update specific configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()