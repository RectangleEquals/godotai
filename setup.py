#!/usr/bin/env python3
"""
GodotAI Build System - Main Entry Point

This script discovers and executes build tools from the tools/ directory.
Each tool is self-describing and can accept custom arguments.

Usage:
    python setup.py             # Interactive menu
    python setup.py <tool>      # Run specific tool (future)
"""

import sys
from typing import Dict, Any, Optional
from pathlib import Path


def clear_screen():
    """Clear the terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def display_header():
    """Display the application header."""
    print("=" * 70)
    print("GodotAI Build System".center(70))
    print("=" * 70)
    print()


def display_menu(tools: list) -> None:
    """
    Display an interactive menu of available tools.
    
    Args:
        tools: List of tool instances
    """
    clear_screen()
    display_header()
    
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name}")
        print(f"   {tool.description}")
        if tool.arguments:
            print(f"   Arguments: {len(tool.arguments)}")
        print()
    
    print("q. Quit")
    print()


def prompt_for_arguments(tool) -> Dict[str, Any]:
    """
    Prompt the user for tool arguments.
    
    Args:
        tool: Tool instance
        
    Returns:
        Dictionary of argument name -> value
    """
    args = {}
    
    if not tool.arguments:
        return args
    
    print(f"\nConfiguration for '{tool.name}':")
    print("-" * 70)
    
    for arg in tool.arguments:
        # Build prompt
        prompt = f"\n{arg.name}"
        
        if arg.description:
            print(f"  {arg.description}")
        
        # Handle choices display - filter out empty strings
        if arg.choices:
            display_choices = [c for c in arg.choices if c != ""]
            if display_choices:
                print(f"  Choices: {', '.join(map(str, display_choices))}")
        
        # Show default, handling empty string specially
        if arg.default is not None:
            if arg.default == "":
                prompt += f" [default: <use config>]"
            else:
                prompt += f" [default: {arg.default}]"
        
        if arg.required:
            prompt += " (required)"
        
        prompt += ": "
        
        # Get input with validation
        while True:
            user_input = input(prompt).strip()
            
            # Use default if empty and default exists
            if not user_input and arg.default is not None:
                value = arg.default
                break
            
            # Handle by type
            if arg.type == bool:
                if user_input.lower() in ['y', 'yes', 'true', '1']:
                    value = True
                    break
                elif user_input.lower() in ['n', 'no', 'false', '0']:
                    value = False
                    break
                elif not user_input and not arg.required:
                    value = False
                    break
                else:
                    print("  Please enter: yes/no (y/n)")
                    
            elif arg.type == int:
                try:
                    value = int(user_input)
                    break
                except ValueError:
                    print("  Please enter a number")
                    
            elif arg.type == list:
                value = [v.strip() for v in user_input.split(',') if v.strip()]
                break
                
            else:  # str
                if user_input or not arg.required:
                    value = user_input
                    break
                else:
                    print("  This field is required")
        
        args[arg.name] = value
    
    print()
    return args


def run_interactive():
    """Run the interactive menu."""
    # Import here to avoid circular imports
    from tools import discover_tools
    
    tools = discover_tools()
    
    if not tools:
        print("❌ Error: No tools found!")
        print("\nMake sure you have tool files in the tools/ directory.")
        return 1
    
    while True:
        display_menu(tools)
        
        choice = input("Select a tool (1-{} or q): ".format(len(tools))).strip().lower()
        
        if choice == 'q':
            print("\nExiting...")
            return 0
        
        # Validate numeric choice
        try:
            index = int(choice) - 1
            if not (0 <= index < len(tools)):
                raise ValueError()
        except ValueError:
            print("\n❌ Invalid selection. Press Enter to continue...")
            input()
            continue
        
        # Get the selected tool
        tool = tools[index]
        
        # Prompt for arguments
        try:
            args = prompt_for_arguments(tool)
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            input("\nPress Enter to continue...")
            continue
        
        # Validate arguments
        valid, error = tool.validate_args(args)
        if not valid:
            print(f"\n❌ Error: {error}")
            input("\nPress Enter to continue...")
            continue
        
        # Execute the tool
        print("-" * 70)
        print(f"Executing '{tool.name}'...")
        print("-" * 70)
        
        try:
            result = tool.execute(args)
        except KeyboardInterrupt:
            print("\n\n❌ Interrupted by user")
            result = 130
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            result = 1
        
        # Show result
        print()
        print("=" * 70)
        if result == 0:
            print(f"✅ '{tool.name}' completed successfully!")
        else:
            print(f"❌ '{tool.name}' failed with exit code {result}")
        print("=" * 70)
        
        input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    try:
        return run_interactive()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())