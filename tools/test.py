"""
Test tool - Verifies the tool system is working.

This is a simple tool to test the tool discovery and execution system.
It doesn't do anything useful - just prints a message.
"""

from tools.base_tool import BaseTool, ToolArgument
from typing import Dict, Any


class TestTool(BaseTool):
    """A simple test tool to verify the system works."""
    
    @property
    def name(self) -> str:
        return "test"
    
    @property
    def description(self) -> str:
        return "Test tool to verify the build system is working"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="message",
                description="A message to display",
                type=str,
                required=False,
                default="Hello from the tool system!"
            ),
            ToolArgument(
                name="repeat",
                description="Number of times to repeat the message",
                type=int,
                required=False,
                default=1
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the test tool."""
        message = args.get("message", "Hello!")
        repeat = args.get("repeat", 1)
        
        print(f"\nTest Tool Execution:")
        print("-" * 50)
        
        for i in range(repeat):
            print(f"{i+1}. {message}")
        
        print("-" * 50)
        print("\nTool system is working correctly! ✅")
        
        return 0