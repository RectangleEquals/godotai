"""
Tool discovery system.

Automatically discovers all tools in the tools/ directory
by finding classes that inherit from BaseTool.
"""

import os
import sys
import importlib.util
from typing import List
from pathlib import Path
from tools.base_tool import BaseTool


def discover_tools() -> List[BaseTool]:
    """
    Discover all tools in the tools/ directory.
    
    Scans all .py files in tools/ and looks for classes that
    inherit from BaseTool (but are not BaseTool itself).
    
    Returns:
        List of instantiated tool objects, sorted by name
    """
    # Avoid circular import
    from tools.base_tool import BaseTool
    
    tools = []
    tools_dir = Path(__file__).parent
    
    # Get all .py files in tools/ directory
    for filepath in tools_dir.glob("*.py"):
        filename = filepath.name
        
        # Skip special files
        if filename in ['__init__.py', 'base_tool.py']:
            continue
        
        # Import the module
        module_name = filename[:-3]  # Remove .py extension
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        
        if spec is None or spec.loader is None:
            continue
        
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Warning: Failed to load tool module '{module_name}': {e}")
            continue
        
        # Find BaseTool subclasses in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a class that inherits from BaseTool
            if (isinstance(attr, type) and 
                issubclass(attr, BaseTool) and 
                attr is not BaseTool):
                try:
                    tool_instance = attr()
                    tools.append(tool_instance)
                except Exception as e:
                    print(f"Warning: Failed to instantiate tool '{attr_name}': {e}")
                    continue
    
    # Sort tools by name
    return sorted(tools, key=lambda t: t.name)


def get_tool_by_name(name: str) -> BaseTool:
    """
    Get a specific tool by name.
    
    Args:
        name: Tool name to find
        
    Returns:
        Tool instance
        
    Raises:
        ValueError: If tool not found
    """
    tools = discover_tools()
    
    for tool in tools:
        if tool.name == name:
            return tool
    
    raise ValueError(f"Tool '{name}' not found")