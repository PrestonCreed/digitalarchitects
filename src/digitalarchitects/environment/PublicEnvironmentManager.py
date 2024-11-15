from typing import Dict, Optional, Any
import logging
from ..core.websocketManager import WebSocketClientManager

class PublicEnvironmentManager:
    def __init__(self):
        self.connection_config = None
        self.ws_manager = None
        
    async def initialize_connection(self, unity_env_id: Optional[str] = None):
        """Initialize connection with automatic or manual configuration"""
        if unity_env_id:
            # Manual configuration with user-provided ID
            self.connection_config = await self._get_manual_config(unity_env_id)
        else:
            # Auto-detection of Unity environment
            self.connection_config = await self._auto_detect_config()
            
        if self.connection_config:
            self.ws_manager = WebSocketClientManager(
                uri=self.connection_config['uri'],
                api_key=self.connection_config['api_key']
            )
            await self.ws_manager.connect()
    
    async def _auto_detect_config(self) -> Optional[Dict[str, str]]:
        """Auto-detect Unity environment configuration"""
        try:
            # Check common local ports
            ports = [8080, 8081, 8082]
            for port in ports:
                uri = f"ws://localhost:{port}/unity"
                if await self._test_connection(uri):
                    return {
                        'uri': uri,
                        'api_key': 'auto-generated-key'  # Generate secure key
                    }
            return None
        except Exception as e:
            self.logger.error(f"Auto-detection failed: {e}")
            return None
    
    async def _get_manual_config(self, env_id: str) -> Dict[str, str]:
        """Get configuration for manually specified environment"""
        # Could fetch from a config service or use standard format
        return {
            'uri': f"ws://localhost:8080/unity/{env_id}",
            'api_key': self._generate_key_for_env(env_id)
        }
    
    @staticmethod
    def _generate_key_for_env(env_id: str) -> str:
        """Generate secure API key for environment"""
        import secrets
        return f"da-{env_id}-{secrets.token_urlsafe(16)}"