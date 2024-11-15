import importlib
import os
from typing import List, Dict, Any
from .base_tool import Tool
import logging

from .tools.place_model_tool import place_model_tool
from .tools.import_model import import_model_tool  # If you have this tool

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.logger = logging.getLogger(__name__)
        self.load_tools()
        self.register_default_tools()  # New method

    def register_default_tools(self):
        """Register built-in tools explicitly"""
        default_tools = [
            place_model_tool,
            # Add other default tools here
        ]
        for tool in default_tools:
            self.register_tool(tool)    

    def load_tools(self):
        """
        Dynamically load tools from the tools directory.
        Now separated from default tools.
        """
        tools_directory = os.path.join(os.path.dirname(__file__), 'tools')
        if not os.path.exists(tools_directory):
            self.logger.warning(f"Tools directory not found: {tools_directory}")
            return

        for root, _, files in os.walk(tools_directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    try:
                        relative_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
                        module_path = f"digitalarchitects.tools.{relative_path[:-3].replace(os.path.sep, '.')}"
                        module = importlib.import_module(module_path)
                        
                        # Look for Tool instances
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, Tool):
                                self.register_tool(attr)
                    except Exception as e:
                        self.logger.error(f"Failed to load tool from {file}: {e}")                    

    def register_tool(self, tool: Tool):
        if tool.name in self.tools:
            raise ValueError(f"Tool with name {tool.name} is already registered.")
        self.tools[tool.name] = tool
        self.logger.info(f"Tool '{tool.name}' registered successfully.")

    def get_tools_for_task(self, task_type: str) -> List[Tool]:
        compatible_tools = [
            tool for tool in self.tools.values() if tool.is_compatible(task_type)
        ]
        self.logger.debug(f"Found {len(compatible_tools)} tools for task '{task_type}'.")
        return compatible_tools

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        tool = self.tools.get(tool_name)
        if tool:
            if self.check_requirements(tool):
                self.logger.info(f"Executing tool '{tool.name}' for task.")
                return tool.execute(**kwargs)
            else:
                raise Exception(f"Requirements not met for tool '{tool.name}'.")
        else:
            raise Exception(f"Tool '{tool_name}' not found.")

    def check_requirements(self, tool: Tool) -> bool:
        """
        Check if the tool's requirements are met.
        Implement actual checks based on the requirements.
        """
        if not tool.requirements:
            return True
        for key, value in tool.requirements.items():
            if key == "software":
                if not self.is_software_available(value):
                    self.logger.warning(f"Requirement not met: {value} not found.")
                    return False
            # Add more requirement checks as needed
        return True

    def is_software_available(self, software_name: str) -> bool:
        """
        Check if the required software is available on the system.
        This is a placeholder implementation and should be replaced with actual logic.
        """
        # Example: Check if a software executable is in PATH
        import shutil
        available = shutil.which(software_name) is not None
        self.logger.debug(f"Software '{software_name}' available: {available}")
        return available

    def list_all_tools(self) -> List[str]:
        tool_names = list(self.tools.keys())
        self.logger.info(f"Listing all tools: {tool_names}")
        return tool_names