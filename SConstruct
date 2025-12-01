#!/usr/bin/env python
"""
GodotAI - SCons Build Script

Builds the GDExtension with godot-cpp, libhv, and libgit2.
"""

import os
import sys
from pathlib import Path

# ========================================
# Helper Functions
# ========================================

def find_sources(directories, extensions):
    """
    Recursively find all source files with given extensions.
    
    Args:
        directories: List of directory paths to search
        extensions: List of file extensions (e.g., ['.cpp', '.c'])
        
    Returns:
        List of source file paths
    """
    sources = []
    for directory in directories:
        if not os.path.exists(directory):
            continue
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    sources.append(os.path.join(root, file))
    return sources


def print_build_info(env):
    """Print build configuration information."""
    print("=" * 70)
    print("GodotAI Build Configuration")
    print("=" * 70)
    print(f"Platform: {env['platform']}")
    print(f"Target: {env['target']}")
    print(f"Architecture: {env['arch']}")
    print(f"C++ Standard: C++17")
    print("=" * 70)


# ========================================
# Configuration
# ========================================

libname = "gdai"
project_dir = "test_project"  # For future testing

# ========================================
# Environment Setup
# ========================================

# Create base environment
env = Environment(tools=["default"], PLATFORM="")

# Load custom configuration if it exists
customs = ["custom.py"]
customs = [os.path.abspath(path) for path in customs]

# Define build options
opts = Variables(customs, ARGUMENTS)
opts.Add("source_dirs", "Source directories (comma-separated)", "src")
opts.Add("include_dirs", "Include directories (comma-separated)", "src")
opts.Add("ext_libs_dir", "External libraries directory", "build_ext_libs")

# Update environment with options
opts.Update(env)
Help(opts.GenerateHelpText(env))

# ========================================
# Check Dependencies
# ========================================

# Check for godot-cpp
godot_cpp_dir = "third_party/godot-cpp"
if not os.path.isdir(godot_cpp_dir) or not os.listdir(godot_cpp_dir):
    print("=" * 70)
    print("ERROR: godot-cpp not found!")
    print("=" * 70)
    print("\nRun: python setup.py")
    print("Then choose: init")
    print("\nThis will initialize all submodules including godot-cpp.")
    print("=" * 70)
    sys.exit(1)

# Check for external libraries
ext_libs_dir = Path(env.get("ext_libs_dir", "build_ext_libs"))
if not ext_libs_dir.exists():
    print("=" * 70)
    print("WARNING: External libraries directory not found!")
    print("=" * 70)
    print(f"\nDirectory: {ext_libs_dir}")
    print("\nRun: python setup.py")
    print("Then choose: build-libhv")
    print("Then choose: build-libgit2")
    print("\nThis will build the required dependencies.")
    print("=" * 70)
    # Don't exit - allow godot-cpp to build first

# ========================================
# Include godot-cpp SConstruct
# ========================================

env = SConscript(f"{godot_cpp_dir}/SConstruct", {"env": env, "customs": customs})

# ========================================
# Configure Include Paths
# ========================================

include_dirs = env.get("include_dirs", "src").split(",")

# Add our include directories
include_dirs.extend([
    "src",
    "src/core",
    "src/server",
    "src/handlers",
    "src/state",
    "src/utils",
])

# Add third-party headers
include_dirs.extend([
    "third_party/libhv/include",
    "third_party/nlohmann_json/include",
    "third_party/libgit2/include",
    "third_party/catch2",
])

env.Append(CPPPATH=include_dirs)

# ========================================
# Configure Libraries
# ========================================

# Add external library directory to search path
env.Append(LIBPATH=[str(ext_libs_dir)])

# Link external libraries
# Platform-specific library names
if env["platform"] == "windows":
    # Windows: .lib files
    env.Append(LIBS=["hv_static", "git2"])
    
    # Windows needs additional system libraries for networking and crypto
    env.Append(LIBS=[
        "ws2_32",      # Winsock (networking)
        "winhttp",     # WinHTTP (for libgit2)
        "crypt32",     # Crypto API (for libgit2)
        "rpcrt4",      # RPC runtime (for libgit2)
    ])
else:
    # Linux/Mac: .a files with 'lib' prefix
    env.Append(LIBS=["hv_static", "git2"])
    
    # Linux/Mac may need pthread
    if env["platform"] == "linux":
        env.Append(LIBS=["pthread"])

# ========================================
# Find Source Files
# ========================================

source_dirs = env.get("source_dirs", "src").split(",")
sources = find_sources(source_dirs, [".cpp", ".c", ".cc", ".cxx"])

if not sources:
    print("=" * 70)
    print("ERROR: No source files found!")
    print("=" * 70)
    print(f"\nSearched in: {source_dirs}")
    print("\nMake sure you have .cpp files in src/core/")
    print("=" * 70)
    sys.exit(1)

print(f"\nFound {len(sources)} source files")

# ========================================
# Determine Output Path
# ========================================

platform = env["platform"]
target = env["target"]
arch = env["arch"]

# Convert target to config name (template_debug -> debug)
if "debug" in target:
    config = "debug"
else:
    config = "release"

# Output directory: build/<platform>/<config>/<arch>/
output_dir = f"build/{platform}/{config}/{arch}"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Library filename
suffix = f".{platform}.{target}.{arch}"
lib_filename = f"{env.subst('$SHLIBPREFIX')}{libname}{suffix}{env.subst('$SHLIBSUFFIX')}"
library_path = os.path.join(output_dir, lib_filename)

# ========================================
# Print Build Info
# ========================================

print_build_info(env)
print(f"\nOutput: {library_path}")
print(f"Sources: {len(sources)} files")
print()

# ========================================
# Build Shared Library
# ========================================

library = env.SharedLibrary(library_path, source=sources)

# ========================================
# Set Default Target
# ========================================

Default(library)

# ========================================
# Optional: Install to Test Project
# ========================================

# Uncomment to auto-install to test project after build
# install_dir = f"{project_dir}/addons/gdai/bin/{platform}/"
# install = env.Install(install_dir, library)
# Default(install)