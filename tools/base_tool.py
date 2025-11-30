"""
Base class for all build tools.

Each tool should inherit from BaseTool and implement:
- name: Short identifier (e.g., 'build', 'clean')
- description: What the tool does
- arguments: List of ToolArgument objects (optional)
- execute(args): Main execution logic
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


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