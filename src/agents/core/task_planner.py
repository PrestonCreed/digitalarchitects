from typing import List, Dict, Any
import asyncio
import logging
from LLMSystem import MessageHandler

class TaskPlanner:
    """Plans and sequences tasks based on a high-level process description"""
    
    def __init__(self):
        self.llm = MessageHandler()
        self.logger = logging.getLogger(__name__)
    
    async def plan_tasks(self, process_description: str, project_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to plan tasks for a given process"""
        prompt = f"""You are a Digital Architect tasked with planning tasks to fulfill the following process:
    
Process Description: {process_description}

Project Context:
{project_context}

Break down the process into a sequential list of tasks required to accomplish it. Each task should include:
- Task Type
- Parameters needed

Return the tasks as a JSON array with each task as a JSON object."""
    
        response = await self.llm.process_message(prompt)
        
        # Assuming the LLM returns a JSON-formatted list of tasks
        try:
            planned_tasks = response.get("analysis", [])
            # Validate that planned_tasks is a list of dicts with 'type' and 'parameters'
            if isinstance(planned_tasks, list) and all(isinstance(task, dict) for task in planned_tasks):
                for task in planned_tasks:
                    if 'type' not in task or 'parameters' not in task:
                        raise ValueError("Each task must have 'type' and 'parameters'.")
                self.logger.debug(f"Planned Tasks: {planned_tasks}")
                return planned_tasks
            else:
                raise ValueError("Invalid task format received from LLM.")
        except Exception as e:
            self.logger.error(f"Error parsing planned tasks: {e}")
            return []