"""
Build orchestrator tool.

Coordinates the building of all components (dependencies + plugin)
in the correct order according to tools/config.json configuration.
"""

from pathlib import Path
from typing import Dict, Any, List

from tools.base_tool import BaseTool, ToolArgument


class BuildTool(BaseTool):
    """Build all components of GodotAI."""
    
    @property
    def name(self) -> str:
        return "build"
    
    @property
    def description(self) -> str:
        return "Build GodotAI (dependencies + plugin)"
    
    @property
    def category(self) -> str:
        return "build"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="rebuild",
                description="Rebuild even if outputs already exist",
                type=bool,
                required=False,
                default=False
            ),
            ToolArgument(
                name="skip_deps",
                description="Skip building dependencies (libgit2, libhv)",
                type=bool,
                required=False,
                default=False
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the build orchestrator."""
        root_dir = self.get_root_dir()
        
        rebuild = args.get("rebuild", False)
        skip_deps = args.get("skip_deps", False)
        
        print("\n" + "=" * 70)
        print("GodotAI Build Orchestrator")
        print("=" * 70)
        print(f"\n  Rebuild: {rebuild}")
        print(f"  Skip Dependencies: {skip_deps}")
        print()
        
        # Get build configuration
        config = self.get_tool_config()
        build_priority = config.get("priority", [])
        skip_if_exists = config.get("skip_if_exists", True)
        rebuild_prompt = config.get("rebuild_prompt", True)
        
        if not build_priority:
            self.print_error("No build priority defined in tools/config.json")
            return 1
        
        # Filter out dependencies if skip_deps is True
        tools_to_build = []
        for tool_name in build_priority:
            # Skip dependency tools if requested
            if skip_deps and tool_name.startswith("build-lib"):
                print(f"⏭️  Skipping {tool_name} (--skip_deps)")
                continue
            
            tools_to_build.append(tool_name)
        
        # Build each component
        for i, tool_name in enumerate(tools_to_build, 1):
            print("\n" + "-" * 70)
            print(f"[{i}/{len(tools_to_build)}] Building: {tool_name}")
            print("-" * 70)
            
            # Check if already built (unless rebuild requested)
            if not rebuild and skip_if_exists:
                if self._check_output_exists(tool_name):
                    if rebuild_prompt:
                        response = input(f"\n{tool_name} output already exists. Rebuild? (y/N): ").strip().lower()
                        if response not in ['y', 'yes']:
                            print(f"✓ Skipping {tool_name}")
                            continue
                    else:
                        print(f"✓ Skipping {tool_name} (already built)")
                        continue
            
            # Execute the build tool
            result = self._execute_build_tool(tool_name)
            
            if result != 0:
                self.print_error(f"Failed to build {tool_name}")
                return result
        
        # Summary
        print("\n" + "=" * 70)
        self.print_success("All components built successfully!")
        print("=" * 70)
        print("\n💡 Next steps:")
        print("  1. Run 'install' to deploy to a Godot project")
        print("  2. Or manually copy plugin/ directory to your project's addons/")
        print()
        
        return 0
    
    def _check_output_exists(self, tool_name: str) -> bool:
        """
        Check if a tool's output already exists.
        
        Args:
            tool_name: Name of the build tool
            
        Returns:
            True if output exists
        """
        root_dir = self.get_root_dir()
        
        # Get tool-specific config
        try:
            tool = self.execute_tool.__self__  # Get self reference
            from tools import get_tool_by_name
            tool_instance = get_tool_by_name(tool_name)
            tool_config = tool_instance.get_tool_config()
        except:
            return False
        
        # Check for output files
        if tool_name == "build-libgit2":
            lib_dir = root_dir / "build_ext_libs"
            import platform
            if platform.system() == "Windows":
                lib_file = lib_dir / "git2.lib"
            else:
                lib_file = lib_dir / "libgit2.a"
            return lib_file.exists()
        
        elif tool_name == "build-libhv":
            lib_dir = root_dir / "build_ext_libs"
            import platform
            if platform.system() == "Windows":
                lib_file = lib_dir / "hv_static.lib"
            else:
                lib_file = lib_dir / "libhv_static.a"
            return lib_file.exists()
        
        elif tool_name == "build-plugin":
            # Check if plugin binary exists in staging
            plugin_bin = root_dir / "plugin" / "bin"
            if not plugin_bin.exists():
                return False
            
            # Check for any library files
            import platform
            system = platform.system()
            
            if system == "Windows":
                pattern = "*.dll"
            elif system == "Darwin":
                pattern = "*.dylib"
            else:
                pattern = "*.so"
            
            # Check in platform-specific subdirectories
            for platform_dir in plugin_bin.iterdir():
                if platform_dir.is_dir():
                    libs = list(platform_dir.glob(pattern))
                    if libs:
                        return True
            
            # Also check root bin directory
            libs = list(plugin_bin.glob(pattern))
            return len(libs) > 0
        
        return False
    
    def _execute_build_tool(self, tool_name: str) -> int:
        """
        Execute a specific build tool.
        
        Args:
            tool_name: Name of the tool to execute
            
        Returns:
            Exit code from the tool
        """
        try:
            # For dependency builds, use default settings
            if tool_name.startswith("build-lib"):
                return self.execute_tool(tool_name, {
                    "config": "Release",
                    "clean": False
                })
            
            # For plugin build, use default settings
            elif tool_name == "build-plugin":
                return self.execute_tool(tool_name, {
                    "platform": "",
                    "target": "",
                    "architecture": "",
                    "precision": "",
                    "jobs": 0,
                    "clean": False,
                    "install": True
                })
            
            else:
                # Generic tool execution
                return self.execute_tool(tool_name, {})
        
        except Exception as e:
            self.print_error(f"Failed to execute {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            return 1