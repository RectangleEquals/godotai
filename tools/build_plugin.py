"""
Build tool using CMake.

Compiles the GDExtension using CMake with godot-cpp integration.
This replaces the SCons-based build system to avoid Python 3.13+ compatibility issues.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolArgument
from tools.config import BuildConfig


class BuildPluginTool(BaseTool):
    """Build the GodotAI plugin using CMake."""
    
    @property
    def name(self) -> str:
        return "build-plugin"
    
    @property
    def category(self) -> str:
        return "build"
    
    @property
    def visible(self) -> bool:
        return False  # Only visible to other tools, not in main menu
    
    @property
    def description(self) -> str:
        return "Build the GodotAI plugin library using CMake"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="platform",
                description="Target platform (empty = auto-detect)",
                type=str,
                required=False,
                default="",
                choices=["", "windows", "linux", "macos"]
            ),
            ToolArgument(
                name="target",
                description="Build target (editor only for this plugin)",
                type=str,
                required=False,
                default="",
                choices=["", "editor"]
            ),
            ToolArgument(
                name="architecture",
                description="Target architecture (empty = auto-detect)",
                type=str,
                required=False,
                default="",
                choices=["", "x86_64", "x86_32", "arm64", "universal"]
            ),
            ToolArgument(
                name="precision",
                description="Floating-point precision (empty = use config)",
                type=str,
                required=False,
                default="",
                choices=["", "single", "double"]
            ),
            ToolArgument(
                name="jobs",
                description="Parallel jobs (0 = auto-detect)",
                type=int,
                required=False,
                default=0
            ),
            ToolArgument(
                name="clean",
                description="Clean build directory before building",
                type=bool,
                required=False,
                default=False
            ),
            ToolArgument(
                name="install",
                description="Copy built library to plugin staging directory",
                type=bool,
                required=False,
                default=True
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the CMake build tool."""
        root_dir = self.get_root_dir()
        build_config = BuildConfig(root_dir)
        
        # Check if initialized
        if not build_config.exists():
            self.print_error("Project not initialized. Run 'init' first.")
            return 1
        
        # Load configuration
        config = build_config.load()
        
        # Get build parameters (command-line overrides config)
        platform = args.get("platform") or self._auto_detect_platform()
        target = args.get("target") or config.get("target", "editor")
        architecture = args.get("architecture") or config.get("architecture", "x86_64")
        precision = args.get("precision") or config.get("precision", "single")
        jobs = args.get("jobs") or config.get("jobs", 0)
        should_clean = args.get("clean", False)
        should_install = args.get("install", True)
        
        # Force editor target (this is an editor-only plugin)
        target = "editor"
        
        print("\n" + "=" * 70)
        print("Building GodotAI Extension with CMake")
        print("=" * 70)
        print(f"\n  Platform: {platform}")
        print(f"  Target: {target}")
        print(f"  Architecture: {architecture}")
        print(f"  Precision: {precision}")
        print(f"  Parallel Jobs: {jobs if jobs > 0 else 'auto'}")
        print(f"  Clean build: {should_clean}")
        print(f"  Install: {should_install}")
        print()
        
        # Check dependencies
        if not self._check_dependencies(root_dir):
            return 1
        
        # Determine build directory
        build_dir = root_dir / "build" / "cmake"
        
        # Clean if requested
        if should_clean and build_dir.exists():
            print("🧹 Cleaning build directory...")
            shutil.rmtree(build_dir)
            print()
        
        # Create build directory
        build_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: CMake Configure
        if not self._cmake_configure(root_dir, build_dir, target, architecture, precision):
            return 1
        
        # Step 2: CMake Build
        if not self._cmake_build(build_dir, jobs):
            return 1
        
        # Step 3: Install (optional)
        if should_install:
            if not self._cmake_install(build_dir):
                return 1
        
        # Step 4: Generate gdai.gdextension file
        print("\n📝 Generating gdai.gdextension...")
        result = self.execute_tool("generate-gdextension", {})
        if result != 0:
            self.print_warning("Failed to generate gdextension file")
            print("You may need to create it manually or reinstall")
        
        # Show summary
        self._show_build_summary(root_dir, build_dir, target, platform, should_install)
        
        print("\n" + "=" * 70)
        self.print_success("Build completed successfully!")
        print("=" * 70)
        
        return 0
    
    def _auto_detect_platform(self) -> str:
        """Auto-detect the current platform."""
        import platform
        system = platform.system()
        
        if system == "Windows":
            return "windows"
        elif system == "Linux":
            return "linux"
        elif system == "Darwin":
            return "macos"
        else:
            return "unknown"
    
    def _check_dependencies(self, root_dir: Path) -> bool:
        """
        Check if required dependencies are available.
        
        Args:
            root_dir: Repository root
            
        Returns:
            True if all dependencies are available
        """
        # Check godot-cpp
        godot_cpp = root_dir / "third_party" / "godot-cpp"
        if not godot_cpp.exists() or not list(godot_cpp.iterdir()):
            self.print_error("godot-cpp not found or empty")
            print("\nRun 'init' to initialize submodules")
            return False
        
        return True
    
    def _cmake_configure(self, root_dir: Path, build_dir: Path, 
                        target: str, architecture: str, precision: str) -> bool:
        """
        Run CMake configure step.
        
        Args:
            root_dir: Repository root
            build_dir: Build directory
            target: Build target (template_debug/template_release/editor)
            architecture: Target architecture
            precision: Floating-point precision
            
        Returns:
            True if successful
        """
        print("⚙️  Configuring with CMake...")
        
        cmake_args = [
            "cmake",
            "-S", str(root_dir),
            "-B", str(build_dir),
            f"-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            f"-DGODOTAI_BUILD_TYPE={target}",
            f"-DGODOTAI_PRECISION={precision}",
        ]
        
        # Platform-specific generator
        import platform
        if platform.system() == "Windows":
            # Use Visual Studio generator on Windows
            cmake_args.extend([
                "-G", "Visual Studio 17 2022",
            ])
            
            # Set architecture for VS
            arch_map = {
                "x86_64": "x64",
                "x86_32": "Win32",
                "arm64": "ARM64",
            }
            if architecture in arch_map:
                cmake_args.extend(["-A", arch_map[architecture]])
        
        # Multi-config generators (Visual Studio, Xcode) don't use CMAKE_BUILD_TYPE
        # Single-config generators (Ninja, Unix Makefiles) require it
        if platform.system() != "Windows":
            # Map target to CMake build type
            cmake_build_type = "Release"
            if "debug" in target.lower():
                cmake_build_type = "Debug"
            
            cmake_args.append(f"-DCMAKE_BUILD_TYPE={cmake_build_type}")
        
        print(f"Command: {' '.join(cmake_args)}\n")
        
        try:
            result = subprocess.run(
                cmake_args,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Show warnings and important messages
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if 'warning' in line.lower() or 'found' in line.lower() or 'godotai' in line.lower():
                        print(line)
            
            self.print_success("CMake configuration complete")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error("CMake configuration failed")
            print(f"\nStdout:\n{e.stdout}")
            print(f"\nStderr:\n{e.stderr}")
            return False
        except FileNotFoundError:
            self.print_error("CMake not found")
            print("\nPlease install CMake:")
            print("  - Windows: https://cmake.org/download/")
            print("  - Linux: sudo apt install cmake")
            print("  - macOS: brew install cmake")
            return False
    
    def _cmake_build(self, build_dir: Path, jobs: int) -> bool:
        """
        Run CMake build step.
        
        Args:
            build_dir: Build directory
            jobs: Number of parallel jobs (0 = auto)
            
        Returns:
            True if successful
        """
        print("\n🔨 Building GodotAI...")
        
        cmake_args = [
            "cmake",
            "--build", str(build_dir),
        ]
        
        # On multi-config generators, specify the config
        import platform
        if platform.system() == "Windows":
            cmake_args.extend(["--config", "Release"])
        
        # Add parallelism
        if jobs > 0:
            cmake_args.extend(["--parallel", str(jobs)])
        else:
            # Let CMake decide based on CPU cores
            cmake_args.append("--parallel")
        
        print(f"Command: {' '.join(cmake_args)}\n")
        
        try:
            # Run build with real-time output
            result = subprocess.run(
                cmake_args,
                cwd=build_dir,
                text=True
            )
            
            if result.returncode == 0:
                print()
                self.print_success("Build complete")
                return True
            else:
                self.print_error(f"Build failed with exit code {result.returncode}")
                return False
                
        except Exception as e:
            self.print_error(f"Build error: {e}")
            return False
    
    def _cmake_install(self, build_dir: Path) -> bool:
        """
        Run CMake install step.
        
        Args:
            build_dir: Build directory
            
        Returns:
            True if successful
        """
        print("\n📦 Installing to plugin/bin...")
        
        cmake_args = [
            "cmake",
            "--install", str(build_dir),
        ]
        
        # On multi-config generators, specify the config
        import platform
        if platform.system() == "Windows":
            cmake_args.extend(["--config", "Release"])
        
        try:
            result = subprocess.run(
                cmake_args,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.print_success("Installation complete")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error("Installation failed")
            print(f"\nStderr:\n{e.stderr}")
            return False
    
    def _show_build_summary(self, root_dir: Path, build_dir: Path, 
                           target: str, platform: str, installed: bool):
        """
        Show a summary of build outputs.
        
        Args:
            root_dir: Repository root
            build_dir: Build directory
            target: Build target
            platform: Target platform
            installed: Whether files were installed
        """
        print("\n" + "=" * 70)
        print("Build Summary")
        print("=" * 70)
        
        # Check build output directory
        bin_dir = build_dir / "bin"
        if bin_dir.exists():
            print("\n📄 Built files in build/cmake/bin:")
            for file in bin_dir.iterdir():
                if file.is_file():
                    size_kb = file.stat().st_size / 1024
                    print(f"  - {file.name} ({size_kb:.1f} KB)")
        
        # Check installed files
        if installed:
            plugin_bin = root_dir / "plugin" / "bin"
            if plugin_bin.exists():
                print("\n📦 Installed files in plugin/bin:")
                for file in plugin_bin.iterdir():
                    if file.is_file():
                        size_kb = file.stat().st_size / 1024
                        print(f"  - {file.name} ({size_kb:.1f} KB)")
        
        # Show next steps
        print("\n💡 Next steps:")
        if not installed:
            print("  1. Run 'build' again with install=True to copy to plugin/bin")
        print("  2. Copy plugin/ directory to your Godot project's addons/")
        print("  3. Enable the plugin in Godot's Project Settings")