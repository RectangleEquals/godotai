"""
Base class for all build tools.

Each tool should inherit from BaseTool and implement:
- name: Short identifier (e.g., 'build', 'clean')
- description: What the tool does
- category: Tool category for organization (optional, defaults to 'misc')
- visible: Whether tool appears in main menu (optional, defaults to True)
- arguments: List of ToolArgument objects (optional)
- execute(args): Main execution logic
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ToolArgument:
    """Describes an argument that a tool accepts."""
    
    name: str
    description: str
    type: type  # str, int, bool, list
    required: bool = False
    default: Any = None
    choices: Optional[List[str]] = None  # For enum-like arguments
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """
        Validate the provided value.
        
        Returns:
            (is_valid, error_message)
        """
        # Check if required and missing
        if self.required and value is None:
            return False, f"'{self.name}' is required"
        
        # If value is None and not required, it's valid
        if value is None:
            return True, ""
        
        # Check type
        if not isinstance(value, self.type):
            return False, f"'{self.name}' must be of type {self.type.__name__}"
        
        # Check choices
        if self.choices and value not in self.choices:
            return False, f"'{self.name}' must be one of: {', '.join(map(str, self.choices))}"
        
        return True, ""


class BaseTool(ABC):
    """
    Base class for all build system tools.
    
    Tools are discovered automatically by scanning the tools/ directory.
    Each tool must implement name, description, and execute().
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Short name for the tool (e.g., 'build', 'clean', 'init').
        Must be lowercase and unique.
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Brief description of what the tool does.
        Displayed in the menu.
        """
        pass
    
    @property
    def category(self) -> str:
        """
        Tool category for organization and filtering.
        
        Common categories:
        - 'init': Initialization and setup
        - 'build': Build operations
        - 'clean': Cleanup operations
        - 'install': Installation operations
        - 'misc': Miscellaneous utilities
        
        Returns:
            Category name (defaults to 'misc')
        """
        return "misc"
    
    @property
    def visible(self) -> bool:
        """
        Whether this tool should be visible in the main menu.
        
        Set to False for tools that are only meant to be called
        by other tools (e.g., build-libgit2 called by build).
        
        Returns:
            True if visible in main menu (default: True)
        """
        return True
    
    @property
    def arguments(self) -> List[ToolArgument]:
        """
        List of arguments this tool accepts.
        Override this if your tool needs arguments.
        
        Returns:
            List of ToolArgument objects
        """
        return []
    
    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> int:
        """
        Execute the tool with provided arguments.
        
        Args:
            args: Dictionary mapping argument name to value
            
        Returns:
            Exit code (0 = success, non-zero = failure)
        """
        pass
    
    def validate_args(self, args: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate all provided arguments.
        
        Args:
            args: Arguments to validate
            
        Returns:
            (all_valid, error_message)
        """
        for arg_def in self.arguments:
            value = args.get(arg_def.name)
            is_valid, error_msg = arg_def.validate(value)
            if not is_valid:
                return False, error_msg
        
        return True, ""
    
    def get_root_dir(self) -> Path:
        """
        Get the repository root directory.
        
        Returns:
            Path to repository root
        """
        # tools/base_tool.py -> tools/ -> root/
        return Path(__file__).parent.parent.resolve()
    
    def get_tool_config(self) -> Dict[str, Any]:
        """
        Get tool-specific configuration from tools/config.json.
        
        Returns:
            Dictionary of configuration for this tool
        """
        config_path = Path(__file__).parent / "config.json"
        
        if not config_path.exists():
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get(self.name, {})
        except Exception as e:
            print(f"Warning: Failed to load tool config: {e}")
            return {}
    
    def discover_tools_by_category(self, category: str) -> List['BaseTool']:
        """
        Discover tools in a specific category.
        
        Args:
            category: Category name to filter by
            
        Returns:
            List of tool instances in the category
        """
        from tools import discover_tools
        
        all_tools = discover_tools(include_hidden=True)
        return [tool for tool in all_tools if tool.category == category]
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any] = None) -> int:
        """
        Execute another tool by name.
        
        Args:
            tool_name: Name of tool to execute
            args: Arguments to pass to the tool
            
        Returns:
            Exit code from the tool
        """
        from tools import get_tool_by_name
        
        if args is None:
            args = {}
        
        try:
            tool = get_tool_by_name(tool_name)
            return tool.execute(args)
        except ValueError as e:
            self.print_error(str(e))
            return 1
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"\n❌ Error: {message}")
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"\n✅ {message}")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"\n⚠️  Warning: {message}")
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"\nℹ️  {message}")