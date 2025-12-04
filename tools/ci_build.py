"""
CI Build Tool

Executes a complete build pipeline for a single platform/architecture.
This tool is designed to be called by CI systems and is hidden from
the interactive menu.
"""

import platform as sys_platform
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
        return True
    
    @property
    def arguments(self) -> List[ToolArgument]:
        return [
            ToolArgument(
                name="godot_version",
                description="Godot version (e.g., '4.4')",
                type=str,
                required=False,
                default="4.4"
            ),
            ToolArgument(
                name="arch",
                description="Target architecture",
                type=str,
                required=False,
                default="x86_64",
                choices=["x86_64", "x86_32", "arm64", "universal"]
            ),
            ToolArgument(
                name="target",
                description="Build target",
                type=str,
                required=False,
                default="editor",
                choices=["editor"]
            ),
            ToolArgument(
                name="build_type",
                description="CMake build type for dependencies",
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
        print(f"Platform: {sys_platform.system()}")
        print(f"Architecture: {args.get('arch', 'x86_64')}")
        print(f"Target: {args.get('target', 'editor')}")
        print(f"Build Type: {args.get('build_type', 'Release')}")
        print("=" * 70)
        
        # Step 1: Initialize (unless skipped)
        if not args.get("skip_init", False):
            print("\n[1/4] Initializing project...")
            result = self.execute_tool("init", {
                "godot_version": args.get("godot_version", "4.4"),  # FIXED: was "version"
                "platform": "",  # Use default
                "config": "",  # Use default
                "architecture": args.get("arch", "x86_64"),  # FIXED: was missing
                "jobs": 4  # FIXED: was missing
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
                "config": build_type,  # Use 'config' not 'build_type'
                "clean": False
            })
            if result != 0:
                self.print_error("libgit2 build failed")
                return result
            print("✅ libgit2 build complete")
            
            print("\n[3/4] Building libhv...")
            result = self.execute_tool("build-libhv", {
                "config": build_type,  # Use 'config' not 'build_type'
                "clean": False
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
            "platform": "",  # Auto-detect
            "target": args.get("target", "editor"),
            "architecture": args.get("arch", "x86_64"),  # Use 'architecture' not 'arch'
            "precision": args.get("precision", "single"),
            "jobs": 0,  # Auto-detect
            "clean": False,
            "install": True  # Install to staging
        })
        
        if result != 0:
            self.print_error("Plugin build failed")
            return result
        
        print("✅ Plugin build complete")
        
        # Show build output location
        print("\n" + "=" * 70)
        self.print_success("CI build pipeline completed successfully!")
        print("=" * 70)
        
        # Show where artifacts are
        root_dir = self.get_root_dir()
        plugin_bin = root_dir / "plugin" / "bin"
        
        if plugin_bin.exists():
            print("\n📦 Built artifacts:")
            for platform_dir in plugin_bin.iterdir():
                if platform_dir.is_dir():
                    print(f"  Platform: {platform_dir.name}")
                    for lib_file in platform_dir.iterdir():
                        if lib_file.is_file():
                            size_mb = lib_file.stat().st_size / (1024 * 1024)
                            print(f"    - {lib_file.name} ({size_mb:.2f} MB)")
        
        return 0