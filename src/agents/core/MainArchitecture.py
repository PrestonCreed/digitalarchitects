from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import asyncio
from LLMSystem import MessageHandler, LLMResponse

@dataclass
class ProcessContext:
    """Context for any ongoing process"""
    user_request: str
    project_context: Dict[str, Any]
    task_history: List[Dict[str, Any]]
    inferred_details: Dict[str, Any]
    confidence_metrics: Dict[str, float]

@dataclass
class TaskResult:
    """Result of a task execution"""
    success: bool
    message: str
    artifacts: Dict[str, Any]
    next_steps: Optional[List[str]] = None
    error: Optional[str] = None

class DigitalArchitect:
    """Main Digital Architect Agent"""
    
    def __init__(self):
        self.llm = MessageHandler()
        self.logger = logging.getLogger(__name__)
        self.tool_manager = ToolManager()
        self.process_memory = []
        self.current_context = None

    async def handle_request(self, message: str, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for handling user requests"""
        try:
            # Initialize process context
            self.current_context = ProcessContext(
                user_request=message,
                project_context=project_context,
                task_history=[],
                inferred_details={},
                confidence_metrics={}
            )

            # Analyze request and determine approach
            understanding = await self._analyze_request()
            
            # Check if we need user clarification
            if understanding.get("needs_clarification") and self._should_ask_user(understanding):
                return self._format_clarification_request(understanding)

            # Execute process/task
            result = await self._execute_request(understanding)
            
            # Only return if complete or if we need user input
            if result.get("needs_user_input"):
                return self._format_user_request(result)
            elif result.get("is_complete"):
                return self._format_completion_response(result)
            else:
                # Continue processing silently
                return {"status": "processing"}

        except Exception as e:
            self.logger.error(f"Error handling request: {str(e)}")
            return {"error": str(e)}

    async def _analyze_request(self) -> Dict[str, Any]:
        """Use LLM to analyze and understand the request"""
        
        prompt = f"""As a Digital Architect, analyze this request comprehensively:

User Request: {self.current_context.user_request}

Project Context:
{self.current_context.project_context}

Consider:
1. Is this a full process or single task?
2. What can be confidently inferred from context?
3. What tools will be needed?
4. What are the potential risks or impacts?

Provide detailed analysis with confidence levels."""

        analysis = await self.llm.process_message(prompt)
        
        # Update context with inferred details
        self.current_context.inferred_details = analysis.get("inferred_details", {})
        self.current_context.confidence_metrics = analysis.get("confidence_metrics", {})
        
        return analysis

    def _should_ask_user(self, understanding: Dict[str, Any]) -> bool:
        """Determine if we should consult user based on impact and confidence"""
        
        # Extract metrics
        impact = understanding.get("impact_metrics", {})
        confidence = understanding.get("confidence_metrics", {})
        
        # High impact/low confidence thresholds
        should_ask = (
            (impact.get("size", 0) > 0.7 and impact.get("importance", 0) > 0.7) or
            confidence.get("context_fit", 1.0) < 0.4 or
            (impact.get("visibility", 0) > 0.7 and confidence.get("style_fit", 1.0) < 0.6)
        )
        
        return should_ask

    async def _execute_request(self, understanding: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the understood request"""
        
        if understanding.get("is_process"):
            return await self._handle_process(understanding)
        else:
            return await self._handle_task(understanding)

    async def _handle_process(self, understanding: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a multi-task process"""
        try:
            tasks = understanding["required_tasks"]
            results = []
            
            for task in tasks:
                result = await self._execute_task(task)
                results.append(result)
                
                if result.get("needs_user_input"):
                    return result
                
            return {
                "is_complete": True,
                "results": results,
                "message": "Process completed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error in process execution: {str(e)}")
            return {"error": str(e)}

    async def _execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a single task"""
        try:
            # Get required tools
            tools = self.tool_manager.get_tools_for_task(task["type"])
            
            # Execute task steps
            for step in task["steps"]:
                result = await self._execute_step(step, tools)
                if not result.success:
                    return result
            
            return TaskResult(
                success=True,
                message="Task completed",
                artifacts=task.get("artifacts", {})
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message="Task failed",
                artifacts={},
                error=str(e)
            )

    def _format_clarification_request(self, understanding: Dict[str, Any]) -> Dict[str, Any]:
        """Format a user clarification request"""
        return {
            "needs_clarification": True,
            "message": understanding["clarification_question"],
            "context": understanding["context"]
        }

    def _format_completion_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a completion response"""
        return {
            "success": True,
            "message": result["message"],
            "artifacts": result.get("artifacts", {})
        }
    
    