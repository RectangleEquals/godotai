"""
Initialize project tool.

Sets up the project by:
- Initializing git submodules
- Checking out correct godot-cpp branch
- Generating build configuration
- Creating compile_commands.json for IDE integration
"""

import subprocess
from pathlib import Path
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolArgument
from tools.config import BuildConfig


class InitTool(BaseTool):
    """Initialize the GodotAI project."""
    
    @property
    def name(self) -> str:
        return "init"
    
    @property
    def description(self) -> str:
        return "Initialize project (submodules, configuration, IDE setup)"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="godot_version",
                description="Godot version to target",
                type=str,
                required=True,
                choices=["4.4", "4.5"]
            ),
            ToolArgument(
                name="platform",
                description="Target platform",
                type=str,
                required=False,
                default="windows",
                choices=["windows", "linux", "macos"]
            ),
            ToolArgument(
                name="config",
                description="Build configuration",
                type=str,
                required=False,
                default="release",
                choices=["debug", "release"]
            ),
            ToolArgument(
                name="architecture",
                description="Target architecture",
                type=str,
                required=False,
                default="x86_64",
                choices=["x86_64", "x86_32", "arm64", "universal"]
            ),
            ToolArgument(
                name="jobs",
                description="Number of parallel build jobs",
                type=int,
                required=False,
                default=4
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the init tool."""
        root_dir = self.get_root_dir()
        
        print("\n" + "=" * 70)
        print("Initializing GodotAI Project")
        print("=" * 70)
        
        # Step 1: Initialize submodules
        if not self._init_submodules(root_dir):
            return 1
        
        # Step 2: Checkout correct godot-cpp branch
        godot_version = args["godot_version"]
        if not self._setup_godot_cpp(root_dir, godot_version):
            return 1
        
        # Step 3: Save configuration
        config = BuildConfig(root_dir)
        config.save({
            "godot_version": godot_version,
            "platform": args["platform"],
            "config": args["config"],
            "architecture": args["architecture"],
            "jobs": args["jobs"],
        })
        
        self.print_success("Configuration saved")
        print(f"\n  Godot Version: {godot_version}")
        print(f"  Platform: {args['platform']}")
        print(f"  Config: {args['config']}")
        print(f"  Architecture: {args['architecture']}")
        print(f"  Parallel Jobs: {args['jobs']}")
        
        # Step 4: Generate compile_commands.json placeholder
        # (Will be generated properly after first build)
        self.print_info("IDE integration will be set up after first build")
        
        print("\n" + "=" * 70)
        self.print_success("Initialization complete!")
        print("\nNext steps:")
        print("  1. Run 'python setup.py' and choose 'build' to compile")
        print("  2. Run 'python setup.py' and choose 'install' to add to a Godot project")
        print("=" * 70)
        
        return 0
    
    def _init_submodules(self, root_dir: Path) -> bool:
        """
        Initialize git submodules.
        
        Args:
            root_dir: Repository root
            
        Returns:
            True if successful
        """
        print("\n📦 Initializing git submodules...")
        
        try:
            result = subprocess.run(
                ["git", "submodule", "update", "--init", "--recursive"],
                cwd=root_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.print_success("Submodules initialized")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to initialize submodules: {e.stderr}")
            return False
        except FileNotFoundError:
            self.print_error("Git not found. Please install Git and try again.")
            return False
    
    def _setup_godot_cpp(self, root_dir: Path, version: str) -> bool:
        """
        Checkout the correct godot-cpp branch.
        
        Args:
            root_dir: Repository root
            version: Godot version (e.g., "4.4")
            
        Returns:
            True if successful
        """
        godot_cpp_dir = root_dir / "third_party" / "godot-cpp"
        
        if not godot_cpp_dir.exists():
            self.print_error("godot-cpp not found. Did submodule init fail?")
            return False
        
        print(f"\n🎮 Setting up godot-cpp for Godot {version}...")
        
        try:
            # Checkout the version branch
            result = subprocess.run(
                ["git", "checkout", version],
                cwd=godot_cpp_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.print_success(f"godot-cpp set to {version} branch")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_warning(f"Could not checkout godot-cpp {version} branch")
            print(f"  Error: {e.stderr.strip()}")
            print(f"  Continuing with current branch...")
            return True  # Non-fatal, continue anyway