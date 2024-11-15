from typing import Dict, List, Any, Optional
from ..tools.tool_registry import ToolRegistry
from ..tools.base_tool import Tool

class ArchitectToolManager:
    """Manages tool access and execution for Digital Architects"""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self.current_task_tools: Dict[str, List[Tool]] = {}
        self.tool_cache: Dict[str, Any] = {}
        self.ws_manager = None  # Will be set by DigitalArchitect
        self.action_results = {}  # Track action results
        
    async def prepare_tools_for_task(self, task_type: str) -> Dict[str, List[Tool]]:
        """Prepare and validate tools needed for a specific task"""
        try:
            # Get compatible tools
            tools = self.registry.get_tools_for_task(task_type)
            
            if not tools:
                raise ValueError(f"No compatible tools found for task: {task_type}")
            
            # Validate all tools are ready
            await self._validate_tools(tools)
            
            # Cache tools for this task
            self.current_task_tools[task_type] = tools
            
            return {
                "task_type": task_type,
                "available_tools": [tool.name for tool in tools],
                "ready": True
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing tools for {task_type}: {e}")
            raise

    async def execute_tool_chain(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced tool chain execution with Unity action support"""
        results = {}
        tools = self.current_task_tools.get(task_type, [])
        
        for tool in tools:
            try:
                if tool.requires_unity_action:
                    # Execute tool through Unity
                    action_result = await self._execute_unity_action(tool, context)
                    results[tool.name] = action_result
                else:
                    # Execute tool locally
                    result = await self._execute_tool_with_context(tool, context)
                    if result.get("success"):
                        self.tool_cache[tool.name] = result
                        results[tool.name] = result
                    
            except Exception as e:
                self.logger.error(f"Error executing tool {tool.name}: {e}")
                raise
                
        return results
    
    async def _execute_unity_action(self, tool: Tool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action through Unity WebSocket"""
        action_data = {
            "action": tool.unity_action_type,
            "parameters": self._prepare_action_parameters(tool, context),
            "tool_id": tool.name
        }
        
        response = await self.ws_manager.send_command(action_data)
        return self._process_unity_response(response)
    
    def _prepare_action_parameters(self, tool: Tool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for Unity action based on context and tool requirements."""
        parameters = {}
        # Map context data to parameters required by the Unity action
        for param in tool.requirements:
            if param in context['inferred_details']:
                parameters[param] = context['inferred_details'][param]
            else:
                raise ValueError(f"Parameter '{param}' is required for tool '{tool.name}'")

        return parameters

    def _process_unity_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process response from Unity and return a standardized result."""
        if response.get('status') == 'success':
            return {
                'success': True,
                'data': response.get('data')
            }
        else:
            return {
                'success': False,
                'error': response.get('error')
            }

    async def _validate_tools(self, tools: List[Tool]) -> bool:
        """Validate all tools are available and requirements are met"""
        for tool in tools:
            if not self.registry.check_requirements(tool):
                raise ValueError(f"Requirements not met for tool: {tool.name}")
        return True

    async def _execute_tool_with_context(self, tool: Tool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool with proper context"""
        try:
            # Prepare context for tool
            tool_context = self._prepare_tool_context(tool, context)
            
            # Execute tool
            result = self.registry.execute_tool(tool.name, **tool_context)
            
            return {
                "success": True,
                "tool": tool.name,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "tool": tool.name,
                "error": str(e)
            }

    def _prepare_tool_context(self, tool: Tool, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context specific to tool requirements"""
        tool_context = {}
        
        # Map general context to tool-specific requirements
        for req in tool.requirements or {}:
            if req in context:
                tool_context[req] = context[req]
                
        return tool_context

    def clear_cache(self, task_type: Optional[str] = None):
        """Clear tool cache for specific task or all tasks"""
        if task_type:
            tools = self.current_task_tools.get(task_type, [])
            for tool in tools:
                self.tool_cache.pop(tool.name, None)
        else:
            self.tool_cache.clear()