"""
CI Build Tool

Executes a complete build pipeline for a single platform/architecture.
This tool is designed to be called by CI systems and is hidden from
the interactive menu.
"""

import platform
from typing import Dict, Any, List
from tools.base_tool import BaseTool, ToolArgument


class CIBuildTool(BaseTool):
    """Single-platform build pipeline for CI environments."""
    
    @property
    def name(self) -> str:
        return "ci-build"
    
    @property
    def description(self) -> str:
        return "CI build pipeline for single platform (init + dependencies + plugin)"
    
    @property
    def category(self) -> str:
        return "build"
    
    @property
    def visible(self) -> bool:
        # Hidden from interactive menu - only for CI use
        return False
    
    @property
    def arguments(self) -> List[ToolArgument]:
        return [
            ToolArgument(
                name="godot_version",
                description="Godot version (e.g., '4.4')",
                type=str,
                required=True
            ),
            ToolArgument(
                name="arch",
                description="Target architecture",
                type=str,
                required=True,
                choices=["x86_64", "x86_32", "arm64", "universal"]
            ),
            ToolArgument(
                name="target",
                description="Build target",
                type=str,
                required=False,
                default="editor",
                choices=["editor", "template_debug", "template_release"]
            ),
            ToolArgument(
                name="build_type",
                description="CMake build type",
                type=str,
                required=False,
                default="Release",
                choices=["Debug", "Release", "RelWithDebInfo"]
            ),
            ToolArgument(
                name="precision",
                description="Floating point precision",
                type=str,
                required=False,
                default="single",
                choices=["single", "double"]
            ),
            ToolArgument(
                name="skip_init",
                description="Skip initialization step (for rebuild)",
                type=bool,
                required=False,
                default=False
            ),
            ToolArgument(
                name="skip_deps",
                description="Skip dependency builds (for rebuild)",
                type=bool,
                required=False,
                default=False
            ),
            ToolArgument(
                name="verbose",
                description="Verbose build output",
                type=bool,
                required=False,
                default=False
            )
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the CI build pipeline for a single platform."""
        
        print("=" * 70)
        print("CI BUILD PIPELINE".center(70))
        print("=" * 70)
        print(f"Platform: {platform.system()}")
        print(f"Architecture: {args['arch']}")
        print(f"Target: {args.get('target', 'editor')}")
        print(f"Build Type: {args.get('build_type', 'Release')}")
        print("=" * 70)
        
        # Step 1: Initialize (unless skipped)
        if not args.get("skip_init", False):
            print("\n[1/4] Initializing project...")
            result = self.execute_tool("init", {
                "version": args["godot_version"],
                "config": "",  # Use default config
                "cpp_bindings_branch": "",  # Use default branch
                "init_submodules": True,
                "force_reinit": False
            })
            if result != 0:
                self.print_error("Initialization failed")
                return result
            print("✅ Initialization complete")
        else:
            print("\n[1/4] ⏭️  Skipping initialization...")
        
        # Step 2: Build dependencies (unless skipped)
        if not args.get("skip_deps", False):
            build_type = args.get("build_type", "Release")
            
            print("\n[2/4] Building libgit2...")
            result = self.execute_tool("build-libgit2", {
                "build_type": build_type,
                "force_rebuild": False
            })
            if result != 0:
                self.print_error("libgit2 build failed")
                return result
            print("✅ libgit2 build complete")
            
            print("\n[3/4] Building libhv...")
            result = self.execute_tool("build-libhv", {
                "build_type": build_type,
                "force_rebuild": False
            })
            if result != 0:
                self.print_error("libhv build failed")
                return result
            print("✅ libhv build complete")
        else:
            print("\n[2/4] ⏭️  Skipping dependencies...")
            print("[3/4] ⏭️  Skipping dependencies...")
        
        # Step 3: Build plugin
        print("\n[4/4] Building plugin...")
        result = self.execute_tool("build-plugin", {
            "config": "",  # Use default config
            "target": args.get("target", "editor"),
            "arch": args["arch"],
            "precision": args.get("precision", "single"),
            "threads": "0",  # Auto-detect
            "verbose": args.get("verbose", False),
            "force_rebuild": True  # Always rebuild in CI
        })
        
        if result != 0:
            self.print_error("Plugin build failed")
            return result
        
        print("✅ Plugin build complete")
        
        print("\n" + "=" * 70)
        self.print_success("CI build pipeline completed successfully!")
        print("=" * 70)
        return 0