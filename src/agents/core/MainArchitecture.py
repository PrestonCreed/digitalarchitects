from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import asyncio
from registry.tool_registry import ToolRegistry
from tools.base_tool import Tool
from prompts.system_prompts import BASE_ROLE, ANALYSIS_PROMPT, CLARIFICATION_PROMPT, COMPLETION_PROMPT
import json

class DigitalArchitect:
    """Main Digital Architect Agent"""
    
    def __init__(self, websocket_uri: str, api_key: str):
        self.llm = MessageHandler(system_prompt=BASE_ROLE)
        self.logger = logging.getLogger(__name__)
        self.tool_manager = ArchitectToolManager()
        self.ws_manager = WebSocketClientManager(websocket_uri, api_key)
        self.tool_manager.ws_manager = self.ws_manager  # Connect components
        self.process_memory = []
        self.current_context = None

    async def start(self):
        """Initialize and start all components"""
        await self.ws_manager.start()
        # Initialize other components as needed    

    async def handle_request(self, message: str, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced request handling with Unity integration"""
        try:
            if not self.ws_manager.is_connected.is_set():
                return {
                    "status": "error",
                    "message": "Unity connection not available"
                }
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
                clarification_question = understanding.get("clarification_question", "Could you please provide more details?")
                return self._format_clarification_request(clarification_question)

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
        
        prompt = ANALYSIS_PROMPT.format(
            user_request=self.current_context.user_request,
            project_context=self._format_project_context(self.current_context.project_context)
        )
        
        analysis_response = await self.llm.process_message(prompt)
        
        try:
            analysis = json.loads(analysis_response)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse analysis response as JSON.")
            analysis = {}
        
        # Update context with inferred details
        self.current_context.inferred_details = analysis.get("inferred_details", {})
        self.current_context.confidence_metrics = analysis.get("confidence_metrics", {})
        
        # Determine if clarification is needed
        needs_clarification = False
        clarification_question = ""
        if "clarification_question" in analysis:
            needs_clarification = True
            clarification_question = analysis["clarification_question"]
        
        analysis.update({
            "needs_clarification": needs_clarification,
            "clarification_question": clarification_question
        })
        
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
                
            # Generate completion message
            completion_message = await self._generate_completion_message(results)
            # Reflect on the task execution
            reflection = await self._reflect_on_tasks(results)
            return {
                "is_complete": True,
                "results": results,
                "message": completion_message,
                "reflection": reflection
            }
            
        except Exception as e:
            self.logger.error(f"Error in process execution: {str(e)}")
            return {"error": str(e)}

    async def _execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a task using appropriate tools"""
        try:
            # Prepare tools for task
            tool_preparation = await self.tool_manager.prepare_tools_for_task(task["type"])
            
            if not tool_preparation["ready"]:
                return TaskResult(
                    success=False,
                    message="Failed to prepare tools",
                    artifacts={},
                    error="Tool preparation failed"
                )

            # Execute tool chain
            tool_results = await self.tool_manager.execute_tool_chain(
                task["type"],
                self.current_context.__dict__
            )
            
            # Process results
            processed_results = self._process_tool_results(tool_results)
            
            return TaskResult(
                success=True,
                message="Task completed successfully",
                artifacts={
                    "tool_results": tool_results,
                    "task_output": processed_results
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return TaskResult(
                success=False,
                message="Task failed",
                artifacts={},
                error=str(e)
            )
        
    def _process_tool_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process and combine results from multiple tools"""
        processed_results = {}
        
        for tool_name, result in results.items():
            if result["success"]:
                processed_results[tool_name] = result["result"]
            
        return processed_results    

    def _format_clarification_request(self, clarification_question: str) -> Dict[str, Any]:
        """Format a user clarification request"""
        return {
            "needs_clarification": True,
            "message": clarification_question,
            "context": self.current_context.project_context
        }
    
    async def _generate_completion_message(self, results: List[TaskResult]) -> str:
        """Generate a completion message based on task results"""
        prompt = COMPLETION_PROMPT.format(result=[result.artifacts for result in results])
        completion_message = await self.llm.process_message(prompt)
        return completion_message

    async def _reflect_on_tasks(self, results: List[TaskResult]) -> str:
        """Generate reflections based on task execution results"""
        prompt = REFLECTION_PROMPT.format(result=[result.artifacts for result in results])
        reflection = await self.llm.process_message(prompt)
        return reflection
    
    def _format_project_context(self, context: Dict[str, Any]) -> str:
        """Format project context for prompt"""
        formatted = []
        for key, value in context.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)