from dataclasses import dataclass
from typing import List, Callable, Any, Dict

@dataclass
class Tool:
    name: str
    supported_tasks: List[str]
    execute: Callable[..., Any]
    requirements: Dict[str, Any] = None
    requires_unity_action: bool = False  # New attribute
    unity_action_type: str = None        # New attribute

    def is_compatible(self, task_type: str) -> bool:
        return task_type in self.supported_tasks