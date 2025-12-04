#!/usr/bin/env python3
"""
GodotAI Build System - Main Entry Point

This script discovers and executes build tools from the tools/ directory.
Each tool is self-describing and can accept custom arguments.

Usage:
    python setup.py                              # Interactive menu
    python setup.py <tool> --non-interactive --args '{...}'  # Non-interactive mode
"""

import sys
import os
import argparse
import json
from typing import Dict, Any, Optional
from pathlib import Path


def is_non_interactive() -> bool:
    """Check if running in non-interactive mode."""
    return (
        os.getenv('CI') == 'true' or 
        os.getenv('GODOTAI_NON_INTERACTIVE') == '1' or
        not sys.stdin.isatty()
    )


def clear_screen():
    """Clear the terminal screen."""
    if not is_non_interactive():
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


def run_non_interactive(tool_name: str, tool_args: Dict[str, Any]) -> int:
    """
    Run a tool non-interactively with provided arguments.
    
    Args:
        tool_name: Name of tool to execute
        tool_args: Pre-filled arguments for the tool
        
    Returns:
        Exit code
    """
    from tools import get_tool_by_name
    
    try:
        tool = get_tool_by_name(tool_name, include_hidden=True)
        
        print(f"🔧 Executing '{tool.name}'...")
        
        # Validate arguments
        valid, error = tool.validate_args(tool_args)
        if not valid:
            print(f"❌ Argument validation failed: {error}", file=sys.stderr)
            return 1
        
        # Execute
        result = tool.execute(tool_args)
        
        if result == 0:
            print(f"✅ '{tool.name}' completed successfully")
        else:
            print(f"❌ '{tool.name}' failed with exit code {result}", file=sys.stderr)
        
        return result
        
    except ValueError as e:
        print(f"❌ Error: Tool '{tool_name}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def run_interactive():
    """Run the interactive menu."""
    # Import here to avoid circular imports
    from tools import discover_tools
    
    # Get ALL tools (including hidden ones for execution)
    all_tools = discover_tools(include_hidden=True)
    
    if not all_tools:
        print("❌ Error: No tools found!")
        print("\nMake sure you have tool files in the tools/ directory.")
        return 1
    
    # Filter to only visible tools for menu display
    visible_tools = [tool for tool in all_tools if tool.visible]
    
    if not visible_tools:
        print("❌ Error: No visible tools found!")
        return 1
    
    while True:
        # Display only visible tools in the menu
        display_menu(visible_tools)
        
        choice = input("Select a tool (1-{} or q): ".format(len(visible_tools))).strip().lower()
        
        if choice == 'q':
            print("\nExiting...")
            return 0
        
        # Validate numeric choice
        try:
            index = int(choice) - 1
            if not (0 <= index < len(visible_tools)):
                raise ValueError()
        except ValueError:
            print("\n❌ Invalid selection. Press Enter to continue...")
            input()
            continue
        
        # Get the selected tool from visible list
        tool = visible_tools[index]
        
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


def parse_cli_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='GodotAI Build System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python setup.py
    
  Non-interactive mode:
    python setup.py ci-build --non-interactive --args '{"godot_version": "4.4", "arch": "x86_64"}'
    python setup.py init --non-interactive --args '{"version": "4.4", "init_submodules": true}'
        """
    )
    
    parser.add_argument('tool', nargs='?', 
                       help='Tool name to execute (omit for interactive mode)')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run in non-interactive mode')
    parser.add_argument('--args', type=str, default='{}',
                       help='JSON string of arguments for the tool')
    
    return parser.parse_args()


def main():
    """Main entry point."""
    try:
        cli_args = parse_cli_args()
        
        # Determine mode
        non_interactive_mode = (
            cli_args.non_interactive or 
            is_non_interactive() or 
            cli_args.tool is not None
        )
        
        # Non-interactive mode
        if cli_args.tool and non_interactive_mode:
            # Parse arguments
            tool_args = {}
            if cli_args.args:
                try:
                    tool_args = json.loads(cli_args.args)
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON arguments: {e}", file=sys.stderr)
                    print(f"Received: {cli_args.args}", file=sys.stderr)
                    return 1
            
            return run_non_interactive(cli_args.tool, tool_args)
        
        # Interactive mode (existing behavior)
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