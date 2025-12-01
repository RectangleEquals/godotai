"""
Build libhv library tool.

Builds the libhv HTTP/event library using CMake.
The built library will be used for the HTTP/SSE server in Phase 4.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolArgument


class BuildLibhvTool(BaseTool):
    """Build the libhv HTTP library."""
    
    @property
    def name(self) -> str:
        return "build-libhv"
    
    @property
    def description(self) -> str:
        return "Build libhv HTTP/event library (required for HTTP server)"
    
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
        """Execute the build-libhv tool."""
        root_dir = self.get_root_dir()
        libhv_dir = root_dir / "third_party" / "libhv"
        build_dir = libhv_dir / "build"
        
        # Check if libhv exists
        if not libhv_dir.exists():
            self.print_error("libhv not found at third_party/libhv")
            print("\nDid you run 'init' to initialize submodules?")
            return 1
        
        config = args.get("config", "Release")
        should_clean = args.get("clean", False)
        
        print("\n" + "=" * 70)
        print("Building libhv")
        print("=" * 70)
        print(f"\n  Source: {libhv_dir}")
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
        if not self._cmake_configure(libhv_dir, build_dir, config):
            return 1
        
        # Step 2: CMake Build
        if not self._cmake_build(build_dir, config):
            return 1
        
        # Step 3: Copy library to build_ext_libs
        if not self._copy_library(root_dir, build_dir, config):
            return 1
        
        print("\n" + "=" * 70)
        self.print_success("libhv built successfully!")
        print("=" * 70)
        
        return 0
    
    def _cmake_configure(self, source_dir: Path, build_dir: Path, config: str) -> bool:
        """
        Run CMake configure step.
        
        Args:
            source_dir: libhv source directory
            build_dir: Build directory
            config: Build configuration (Debug/Release)
            
        Returns:
            True if successful
        """
        print("⚙️  Configuring libhv with CMake...")
        
        cmake_args = [
            "cmake",
            "-S", str(source_dir),
            "-B", str(build_dir),
            f"-DCMAKE_BUILD_TYPE={config}",
            "-DBUILD_SHARED=OFF",  # Static library
            "-DBUILD_STATIC=ON",
            "-DWITH_OPENSSL=OFF",  # We don't need SSL for local HTTP
            "-DWITH_NGHTTP2=OFF",  # We don't need HTTP/2
            "-DWITH_KCP=OFF",      # We don't need KCP protocol
        ]
        
        # Platform-specific settings
        import platform
        if platform.system() == "Windows":
            # Use Visual Studio generator on Windows
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
        print("\n🔨 Building libhv...")
        
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
                self.print_success("libhv build complete")
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
        # Windows: hv_static.lib in build/lib/<Config>/
        # Linux/Mac: libhv_static.a in build/lib/
        
        lib_candidates = [
            build_dir / "lib" / config / "hv_static.lib",  # Windows
            build_dir / "lib" / "hv_static.lib",            # Windows alt
            build_dir / "lib" / config / "libhv_static.a",  # Linux/Mac
            build_dir / "lib" / "libhv_static.a",           # Linux/Mac alt
            build_dir / "lib" / config / "libhv.a",         # Alternative name
            build_dir / "lib" / "libhv.a",                  # Alternative name
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