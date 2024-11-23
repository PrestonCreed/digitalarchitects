from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
import uuid
import datetime
from ..utils.logging_config import LoggerMixin, LoggingManager
from ..memory.MemorySystem import MemoryManager, CollectiveMemory
from ..core.MainArchitecture import DigitalArchitect
from ..config.ConfigManager import ConfigManager
from .ArchitectState import AgentState, AgentStateManager, UnityStateSync

@dataclass
class ArchitectGoals:
    """Defines an architect's goals and directives"""
    primary_objective: str
    sub_objectives: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    priority_level: int = 1  # 1-5, 5 being highest priority

@dataclass
class ProjectContext:
    """Project-wide context and shared information"""
    project_id: str
    name: str
    description: str
    shared_context: Dict[str, Any] = field(default_factory=dict)
    architect_relationships: Dict[str, Set[str]] = field(default_factory=dict)  # Maps architects to their collaborators

@dataclass
class ArchitectInstance:
    """Represents a single Digital Architect instance"""
    instance_id: str
    name: str
    architect: DigitalArchitect
    goals: Optional[ArchitectGoals] = None
    status: str = "active"
    created_at: float = field(default_factory=lambda: datetime.datetime.now().timestamp())
    last_active: float = field(default_factory=lambda: datetime.datetime.now().timestamp())
    collaboration_focus: Dict[str, Any] = field(default_factory=dict)  # Areas of focus for collaboration

class InstanceManager(LoggerMixin):
    def __init__(self, config: ConfigManager, project_id: str):
        # Initialize logging first
        LoggingManager(config)  # Ensure logging is set up
        
        self.config = config
        self.project_id = project_id
        self.instances: Dict[str, ArchitectInstance] = {}
        self.collective_memory = CollectiveMemory(project_id)
        
        # State Management
        self.state_manager = AgentStateManager(project_id)
        self.unity_sync = UnityStateSync(self.config.get_websocket_manager())
        
        # Project Context
        self.project_context = ProjectContext(
            project_id=project_id,
            name=f"Project_{project_id}",
            description="Digital Architects Project"
        )
        
        self.logger.info(f"Initialized InstanceManager for project {project_id}")

    async def create_instance(
        self,
        name: str,
        primary_objective: Optional[str] = None,
        sub_objectives: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        collaboration_focus: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new Digital Architect instance"""
        try:
            instance_id = str(uuid.uuid4())
            
            # Create the architect
            architect = DigitalArchitect(
                websocket_uri=self.config.get_websocket_config().uri,
                api_key=self.config.get_websocket_config().api_key,
                architect_id=instance_id,
                project_id=self.project_id
            )

            # Create goals
            goals = ArchitectGoals(
                primary_objective=primary_objective or "No primary objective set",
                sub_objectives=sub_objectives or [],
                constraints=constraints or []
            )

            # Create instance
            instance = ArchitectInstance(
                instance_id=instance_id,
                name=name,
                architect=architect,
                goals=goals,
                collaboration_focus=collaboration_focus or {}
            )

            # Initialize state
            agent_state = AgentState(
                instance_id=instance_id,
                name=name,
                created_at=instance.created_at,
                last_active=instance.last_active,
                status="active",
                llm_config=self.config.get_llm_config(),
                memory_config={"type": "persistent"},
                websocket_config=self.config.get_websocket_config(),
                goals=asdict(goals),
                memory_state={},
                collaborator_ids=set()
            )
            
            await self.state_manager.register_agent(agent_state)

            # Add to project context
            self.project_context.architect_relationships[instance_id] = set()
            await self._update_collaborations(instance_id, collaboration_focus)

            # Store instance
            self.instances[instance_id] = instance
            
            # Initialize architect
            await architect.start()
            
            self.logger.info(f"Created new architect instance: {name} ({instance_id})")
            return instance_id

        except Exception as e:
            self.logger.error(f"Failed to create architect instance: {e}")
            raise

    async def _update_collaborations(self, instance_id: str, focus: Dict[str, Any]):
        """Update collaboration relationships based on focus areas"""
        instance = self.instances[instance_id]
        
        # Find potential collaborators based on focus overlap
        for other_id, other in self.instances.items():
            if other_id != instance_id:
                collaboration_strength = self._calculate_collaboration_strength(
                    focus,
                    other.collaboration_focus
                )
                
                if collaboration_strength > 0.5:  # Threshold for collaboration
                    # Update relationships
                    self.project_context.architect_relationships[instance_id].add(other_id)
                    self.project_context.architect_relationships[other_id].add(instance_id)
                    
                    # Update states
                    await self._notify_collaboration(instance_id, other_id)

    def _calculate_collaboration_strength(self, focus1: Dict[str, Any], focus2: Dict[str, Any]) -> float:
        """Calculate how strongly two architects should collaborate"""
        if not focus1 or not focus2:
            return 0.0
            
        overlap_score = 0.0
        
        # Check area overlap
        if focus1.get("area") == focus2.get("area"):
            overlap_score += 0.4
            
        # Check task type overlap
        if focus1.get("task_type") == focus2.get("task_type"):
            overlap_score += 0.3
            
        # Check location overlap
        if focus1.get("location") == focus2.get("location"):
            overlap_score += 0.3
            
        return overlap_score

    async def _notify_collaboration(self, architect1_id: str, architect2_id: str):
        """Notify architects of collaboration opportunity"""
        # Update states
        await self.state_manager.update_agent_state(architect1_id, {
            "collaborator_ids": self.project_context.architect_relationships[architect1_id]
        })
        
        await self.state_manager.update_agent_state(architect2_id, {
            "collaborator_ids": self.project_context.architect_relationships[architect2_id]
        })
        
        # Add to collective memory
        await self.collective_memory.add_collective_knowledge(
            category="collaborations",
            content={
                "architects": [architect1_id, architect2_id],
                "established": datetime.datetime.now().timestamp()
            },
            contributor_id="system"
        )                

    async def handle_request(self, instance_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a request with state management"""
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
            
        # Get current state
        state = self.state_manager.get_agent_state(instance_id)
        if state.status != "active":
            raise ValueError(f"Instance {instance_id} is not active")

        # Add project context
        context["project"] = self.project_context.__dict__
        context["collaborators"] = list(self.project_context.architect_relationships[instance_id])

        # Update state
        now = datetime.datetime.now().timestamp()
        await self.state_manager.update_agent_state(instance_id, {
            "last_active": now,
            "current_task": {"type": "process_request", "message": message}
        })
        
        # Process request
        response = await instance.architect.handle_request(message, context)
        
        # Update state with response
        await self.state_manager.update_agent_state(instance_id, {
            "last_response": response,
            "current_task": None
        })
        
        return response

    async def pause_instance(self, instance_id: str):
        """Pause an architect instance"""
        instance = self.instances.get(instance_id)
        if instance:
            instance.status = "paused"
            await self.collective_memory.update_architect_role(
                instance_id,
                "paused",
                instance.goals.sub_objectives if instance.goals else [],
                []
            )

    async def resume_instance(self, instance_id: str):
        """Resume a paused architect"""
        instance = self.instances.get(instance_id)
        if instance:
            instance.status = "active"
            instance.last_active = datetime.datetime.now().timestamp()
            await self.collective_memory.update_architect_role(
                instance_id,
                "active",
                instance.goals.sub_objectives if instance.goals else [],
                []
            )

    async def terminate_instance(self, instance_id: str):
        """Permanently terminate an architect instance"""
        instance = self.instances.get(instance_id)
        if instance:
            # Remove from groups
            for group_id in instance.group_ids:
                if group_id in self.groups:
                    self.groups[group_id].architect_ids.remove(instance_id)

            # Update status and collective memory
            instance.status = "terminated"
            await self.collective_memory.update_architect_role(
                instance_id,
                "terminated",
                [],
                []
            )

            # Close connections
            await instance.architect.ws_manager.disconnect()


    async def update_instance_goals(
        self,
        instance_id: str,
        primary_objective: Optional[str] = None,
        sub_objectives: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        priority: Optional[int] = None
    ):
        """Update an architect's goals"""
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")

        if not instance.goals:
            instance.goals = ArchitectGoals(
                primary_objective=primary_objective or "No primary objective set",
                sub_objectives=sub_objectives or [],
                constraints=constraints or [],
                priority_level=priority or 1
            )
        else:
            if primary_objective:
                instance.goals.primary_objective = primary_objective
            if sub_objectives is not None:
                instance.goals.sub_objectives = sub_objectives
            if constraints is not None:
                instance.goals.constraints = constraints
            if priority is not None:
                instance.goals.priority_level = priority

        # Update in collective memory
        await self.collective_memory.update_architect_role(
            instance_id,
            "goals_updated",
            instance.goals.sub_objectives,
            [{"primary_objective": instance.goals.primary_objective}]
        )