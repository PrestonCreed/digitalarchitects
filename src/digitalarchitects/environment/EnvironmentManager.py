from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from ..core.websocketManager import WebSocketClientManager
from typing import Dict, List, Optional, Any

class EnvironmentActionType(Enum):
    IMPORT_MODEL = "import_model"
    PLACE_MODEL = "place_model"
    MODIFY_TERRAIN = "modify_terrain"
    ANALYZE_AREA = "analyze_area"
    GET_STATE = "get_state"
    UPDATE_STATE = "update_state"

@dataclass
class EnvironmentAction:
    """Represents an action to be performed in the Unity environment"""
    action_type: EnvironmentActionType
    parameters: Dict[str, Any]
    agent_id: str
    required_permissions: List[str]

@dataclass
class ActionResult:
    """Result of an environment action"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class EnvironmentState:
    """Tracks and manages environment state"""
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.observers: List[callable] = []
        self.lock = asyncio.Lock()
    
    async def update(self, updates: Dict[str, Any]):
        """Update state with new information"""
        async with self.lock:
            self.state.update(updates)
            await self._notify_observers(updates)
    
    async def _notify_observers(self, updates: Dict[str, Any]):
        """Notify observers of state changes"""
        for observer in self.observers:
            await observer(updates)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        return self.state.copy()

class EnvironmentManager:
    """Manages interaction with Unity environment"""
    
    def __init__(self, websocket_manager, agent_id: str):
        self.websocket = websocket_manager
        self.agent_id = agent_id
        self.state = EnvironmentState()
        self.logger = logging.getLogger(__name__)
        self.active = False
    
    async def start(self):
        """Start environment management"""
        self.active = True
        await asyncio.gather(
            self._monitor_environment(),
            self._process_state_updates()
        )
    
    async def stop(self):
        """Stop environment management"""
        self.active = False
    
    async def execute_action(self, action: EnvironmentAction) -> ActionResult:
        """Execute an action in the Unity environment"""
        try:
            # Format action for Unity
            command = self._format_action_command(action)
            
            # Send to Unity
            response = await self.websocket.send_command(command)
            
            # Process response
            return self._process_action_response(response)
            
        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            return ActionResult(success=False, error=str(e))
    
    async def _monitor_environment(self):
        """Continuously monitor environment state"""
        while self.active:
            try:
                # Get state updates from Unity
                updates = await self.websocket.receive_state()
                if updates:
                    await self.state.update(updates)
            except Exception as e:
                self.logger.error(f"Error monitoring environment: {e}")
            await asyncio.sleep(0.1)
    
    def _format_action_command(self, action: EnvironmentAction) -> Dict[str, Any]:
        """Format action for Unity consumption"""
        return {
            "action_type": action.action_type.value,
            "parameters": action.parameters,
            "agent_id": self.agent_id,
            "required_permissions": action.required_permissions
        }
    
    def _process_action_response(self, response: Dict[str, Any]) -> ActionResult:
        """Process response from Unity"""
        return ActionResult(
            success=response.get("success", False),
            data=response.get("data"),
            error=response.get("error")
        )

class EnvironmentAgent:
    """Base class for agents that interact with the environment"""
    
    def __init__(self, environment_manager: EnvironmentManager):
        self.env_manager = environment_manager
        self.logger = logging.getLogger(__name__)
        self.current_task = None
    
    async def start_autonomous_mode(self):
        """Start autonomous operation in environment"""
        try:
            await self.env_manager.start()
            while True:
                # Get current state
                state = self.env_manager.state.get_state()
                
                # Analyze state and plan actions
                actions = await self._plan_actions(state)
                
                # Execute planned actions
                for action in actions:
                    result = await self.env_manager.execute_action(action)
                    if not result.success:
                        await self._handle_action_failure(action, result)
                        break
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Error in autonomous mode: {e}")
        finally:
            await self.env_manager.stop()
    
    async def execute_task(self, task: Dict[str, Any]):
        """Execute a specific task"""
        self.current_task = task
        try:
            # Convert task to actions
            actions = await self._task_to_actions(task)
            
            # Execute each action
            results = []
            for action in actions:
                result = await self.env_manager.execute_action(action)
                results.append(result)
                if not result.success:
                    await self._handle_action_failure(action, result)
                    break
            
            return results
            
        finally:
            self.current_task = None
    
    async def _plan_actions(self, state: Dict[str, Any]) -> List[EnvironmentAction]:
        """Plan actions based on current state"""
        # Override in specific agent implementations
        raise NotImplementedError
    
    async def _task_to_actions(self, task: Dict[str, Any]) -> List[EnvironmentAction]:
        """Convert a task to a list of environment actions"""
        # Override in specific agent implementations
        raise NotImplementedError
    
    async def _handle_action_failure(self, action: EnvironmentAction, result: ActionResult):
        """Handle action failure"""
        self.logger.error(f"Action failed: {action.action_type} - {result.error}")
        # Implement recovery logic in specific agent implementations
