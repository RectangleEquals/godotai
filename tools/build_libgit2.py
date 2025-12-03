"""
Build libgit2 library tool.

Builds the libgit2 git operations library using CMake.
The built library will be used for git integration in Phase 6.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolArgument


class BuildLibgit2Tool(BaseTool):
    """Build the libgit2 library."""
    
    @property
    def name(self) -> str:
        return "build-libgit2"
    
    @property
    def description(self) -> str:
        return "Build libgit2 git operations library (required for git integration)"
    
    @property
    def category(self) -> str:
        return "build"
    
    @property
    def visible(self) -> bool:
        return False  # Hidden from main menu, called by build orchestrator
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="config",
                description="Build configuration",
                type=str,
                required=False,
                default="Release",
                choices=["Debug", "Release"]
            ),
            ToolArgument(
                name="clean",
                description="Clean build directory before building",
                type=bool,
                required=False,
                default=False
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the build-libgit2 tool."""
        root_dir = self.get_root_dir()
        libgit2_dir = root_dir / "third_party" / "libgit2"
        build_dir = libgit2_dir / "build"
        
        # Check if libgit2 exists
        if not libgit2_dir.exists():
            self.print_error("libgit2 not found at third_party/libgit2")
            print("\nDid you run 'init' to initialize submodules?")
            return 1
        
        config = args.get("config", "Release")
        should_clean = args.get("clean", False)
        
        print("\n" + "=" * 70)
        print("Building libgit2")
        print("=" * 70)
        print(f"\n  Source: {libgit2_dir}")
        print(f"  Config: {config}")
        print(f"  Clean build: {should_clean}")
        print()
        
        # Clean if requested
        if should_clean and build_dir.exists():
            print("🧹 Cleaning build directory...")
            shutil.rmtree(build_dir)
        
        # Create build directory
        build_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: CMake Configure
        if not self._cmake_configure(libgit2_dir, build_dir, config):
            return 1
        
        # Step 2: CMake Build
        if not self._cmake_build(build_dir, config):
            return 1
        
        # Step 3: Copy library to build_ext_libs
        if not self._copy_library(root_dir, build_dir, config):
            return 1
        
        print("\n" + "=" * 70)
        self.print_success("libgit2 built successfully!")
        print("=" * 70)
        
        return 0
    
    def _cmake_configure(self, source_dir: Path, build_dir: Path, config: str) -> bool:
        """
        Run CMake configure step.
        
        Args:
            source_dir: libgit2 source directory
            build_dir: Build directory
            config: Build configuration (Debug/Release)
            
        Returns:
            True if successful
        """
        print("⚙️  Configuring libgit2 with CMake...")
        
        cmake_args = [
            "cmake",
            "-S", str(source_dir),
            "-B", str(build_dir),
            f"-DCMAKE_BUILD_TYPE={config}",
            "-DBUILD_SHARED_LIBS=OFF",  # Static library
            "-DUSE_SSH=OFF",            # No SSH support needed
            "-DUSE_HTTPS=OFF",          # No HTTPS needed for local repos
            "-DBUILD_TESTS=OFF",        # Don't build tests
            "-DBUILD_CLI=OFF",          # Don't build CLI tool (causes zlib errors)
            "-DTHREADSAFE=ON",          # Thread-safe operations
        ]
        
        # Platform-specific settings
        import platform
        if platform.system() == "Windows":
            cmake_args.extend([
                "-G", "Visual Studio 17 2022",
                "-A", "x64"
            ])
        
        try:
            result = subprocess.run(
                cmake_args,
                capture_output=True,
                text=True,
                check=True
            )
            
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
    
    def _cmake_build(self, build_dir: Path, config: str) -> bool:
        """
        Run CMake build step.
        
        Args:
            build_dir: Build directory
            config: Build configuration
            
        Returns:
            True if successful
        """
        print("\n🔨 Building libgit2...")
        
        cmake_args = [
            "cmake",
            "--build", str(build_dir),
            "--config", config,
            "--parallel", "4"
        ]
        
        try:
            # Run build with real-time output
            result = subprocess.run(
                cmake_args,
                cwd=build_dir,
                text=True
            )
            
            if result.returncode == 0:
                self.print_success("libgit2 build complete")
                return True
            else:
                self.print_error(f"Build failed with exit code {result.returncode}")
                return False
                
        except Exception as e:
            self.print_error(f"Build error: {e}")
            return False
    
    def _copy_library(self, root_dir: Path, build_dir: Path, config: str) -> bool:
        """
        Copy built library to build_ext_libs.
        
        Args:
            root_dir: Repository root
            build_dir: Build directory
            config: Build configuration
            
        Returns:
            True if successful
        """
        print("\n📦 Copying library to build_ext_libs...")
        
        # Create output directory
        output_dir = root_dir / "build_ext_libs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find the library file
        # Windows: git2.lib in build/<Config>/
        # Linux/Mac: libgit2.a in build/
        
        lib_candidates = [
            build_dir / config / "git2.lib",      # Windows
            build_dir / "git2.lib",               # Windows alt
            build_dir / config / "libgit2.a",     # Linux/Mac
            build_dir / "libgit2.a",              # Linux/Mac alt
        ]
        
        lib_file = None
        for candidate in lib_candidates:
            if candidate.exists():
                lib_file = candidate
                break
        
        if not lib_file:
            self.print_error("Could not find built library")
            print("\nSearched for:")
            for candidate in lib_candidates:
                print(f"  - {candidate}")
            return False
        
        # Copy to output directory
        output_file = output_dir / lib_file.name
        shutil.copy2(lib_file, output_file)
        
        size_kb = output_file.stat().st_size / 1024
        self.print_success(f"Copied {lib_file.name} ({size_kb:.1f} KB)")
        print(f"  Location: {output_file}")
        
        return True