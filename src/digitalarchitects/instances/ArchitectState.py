from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
import datetime
import json
from pathlib import Path
import asyncio
from ..utils.logging_config import LoggerMixin

@dataclass
class AgentState:
    """Core agent state maintained by Python"""
    instance_id: str
    name: str
    created_at: float
    last_active: float
    status: str  # active, paused, terminated
    
    # Agent Configuration
    llm_config: Dict[str, Any]
    memory_config: Dict[str, Any]
    websocket_config: Dict[str, Any]
    
    # Core State
    goals: Dict[str, Any]
    memory_state: Dict[str, Any]
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    collaborator_ids: Set[str] = field(default_factory=set)
    
    # Current Processing State
    current_task: Optional[Dict[str, Any]] = None
    pending_tasks: List[Dict[str, Any]] = field(default_factory=list)
    last_response: Optional[Dict[str, Any]] = None

class AgentStateManager(LoggerMixin):
    """Manages Python-side agent states"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.states: Dict[str, AgentState] = {}
        self.state_change_callbacks: List[callable] = []
        self.logger = logging.getLogger(__name__)
        
    async def register_agent(self, agent_state: AgentState):
        """Register a new agent's state"""
        self.states[agent_state.instance_id] = agent_state
        await self._notify_state_change(agent_state.instance_id, "registered")
        
    async def update_agent_state(self, instance_id: str, updates: Dict[str, Any]):
        """Update an agent's state"""
        if instance_id not in self.states:
            raise ValueError(f"Agent {instance_id} not found")
            
        state = self.states[instance_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
        
        state.last_active = datetime.datetime.now().timestamp()
        await self._notify_state_change(instance_id, "updated")
        
    async def _notify_state_change(self, instance_id: str, change_type: str):
        """Notify listeners of state changes"""
        for callback in self.state_change_callbacks:
            try:
                await callback(instance_id, change_type, self.states[instance_id])
            except Exception as e:
                self.logger.error(f"Error in state change callback: {e}")

    def add_state_listener(self, callback: callable):
        """Add a listener for state changes"""
        self.state_change_callbacks.append(callback)

    def get_agent_state(self, instance_id: str) -> Optional[AgentState]:
        """Get current state of an agent"""
        return self.states.get(instance_id)

class UnityStateSync:
    """Handles synchronization with Unity's action state"""
    
    def __init__(self, websocket_manager):
        self.ws_manager = websocket_manager
        self.action_states: Dict[str, Dict[str, Any]] = {}
        self.pending_syncs: Dict[str, asyncio.Event] = {}
        
    async def notify_unity_state_change(self, instance_id: str, action_state: Dict[str, Any]):
        """Receive state update from Unity"""
        self.action_states[instance_id] = action_state
        
        # If waiting for sync, notify
        if instance_id in self.pending_syncs:
            self.pending_syncs[instance_id].set()
            
    async def wait_for_unity_state(self, instance_id: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Wait for Unity to report state for an agent"""
        event = asyncio.Event()
        self.pending_syncs[instance_id] = event
        
        try:
            await asyncio.wait_for(event.wait(), timeout)
            return self.action_states.get(instance_id)
        except asyncio.TimeoutError:
            return None
        finally:
            self.pending_syncs.pop(instance_id, None)
            
    async def send_state_update(self, instance_id: str, state_update: Dict[str, Any]):
        """Send state update to Unity"""
        message = {
            "type": "state_update",
            "instance_id": instance_id,
            "state": state_update
        }
        await self.ws_manager.send_command(message)