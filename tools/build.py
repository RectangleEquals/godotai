"""
Build tool.

Compiles the GDExtension using SCons with the configured settings.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolArgument
from tools.config import BuildConfig


class BuildTool(BaseTool):
    """Build the GDExtension."""
    
    @property
    def name(self) -> str:
        return "build"
    
    @property
    def description(self) -> str:
        return "Build the GDExtension library"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="platform",
                description="Target platform (empty = use config)",
                type=str,
                required=False,
                default="",
                choices=["", "windows", "linux", "macos"]
            ),
            ToolArgument(
                name="config",
                description="Build configuration (empty = use config)",
                type=str,
                required=False,
                default="",
                choices=["", "debug", "release"]
            ),
            ToolArgument(
                name="architecture",
                description="Target architecture (empty = use config)",
                type=str,
                required=False,
                default="",
                choices=["", "x86_64", "x86_32", "arm64", "universal"]
            ),
            ToolArgument(
                name="jobs",
                description="Parallel jobs (0 = use config)",
                type=int,
                required=False,
                default=0
            ),
            ToolArgument(
                name="compiledb",
                description="Generate compile_commands.json for IDE",
                type=bool,
                required=False,
                default=True
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the build tool."""
        root_dir = self.get_root_dir()
        build_config = BuildConfig(root_dir)
        
        # Check if initialized
        if not build_config.exists():
            self.print_error("Project not initialized. Run 'init' first.")
            return 1
        
        # Load configuration
        config = build_config.load()
        
        # Get build parameters (command-line overrides config)
        platform = args.get("platform") or config.get("platform", "windows")
        build_type = args.get("config") or config.get("config", "release")
        architecture = args.get("architecture") or config.get("architecture", "x86_64")
        jobs = args.get("jobs") or config.get("jobs", 4)
        compiledb = args.get("compiledb", True)
        
        print("\n" + "=" * 70)
        print("Building GodotAI Extension")
        print("=" * 70)
        print(f"\n  Platform: {platform}")
        print(f"  Config: {build_type}")
        print(f"  Architecture: {architecture}")
        print(f"  Parallel Jobs: {jobs}")
        print(f"  Generate compile_commands.json: {compiledb}")
        print()
        
        # Build SCons command
        # Note: We'll create SConstruct in Phase 3
        scons_args = [
            "scons",
            f"platform={platform}",
            f"target=template_{build_type}",
            f"arch={architecture}",
            f"-j{jobs}",
        ]
        
        if compiledb:
            scons_args.append("compiledb=yes")
        
        print("🔨 Running SCons...")
        print(f"Command: {' '.join(scons_args)}\n")
        
        # Execute SCons
        try:
            result = subprocess.run(
                scons_args,
                cwd=root_dir,
                text=True
            )
            
            if result.returncode == 0:
                print("\n" + "=" * 70)
                self.print_success("Build completed successfully!")
                
                # Show output location
                output_dir = root_dir / "build" / platform / build_type / architecture
                if output_dir.exists():
                    print(f"\nOutput directory: {output_dir}")
                    print("\nBuilt files:")
                    for file in output_dir.iterdir():
                        if file.is_file():
                            size_kb = file.stat().st_size / 1024
                            print(f"  📄 {file.name} ({size_kb:.1f} KB)")
                
                if compiledb:
                    compile_commands = root_dir / "compile_commands.json"
                    if compile_commands.exists():
                        print(f"\n📋 Generated: compile_commands.json (for IDE)")
                
                print("=" * 70)
                return 0
            else:
                print("\n" + "=" * 70)
                self.print_error(f"Build failed with exit code {result.returncode}")
                print("=" * 70)
                return result.returncode
                
        except FileNotFoundError:
            self.print_error("SCons not found. Please install SCons:")
            print("\n  pip install scons")
            print("  OR")
            print("  Visit: https://scons.org/pages/download.html")
            return 1
        except Exception as e:
            self.print_error(f"Build error: {e}")
            return 1