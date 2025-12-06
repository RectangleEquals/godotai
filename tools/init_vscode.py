"""
Initialize VS Code workspace tool.

Generates VS Code configuration files for optimal C++ development:
- compile_commands.json for clangd
- settings.json with clangd configuration
- c_cpp_properties.json as fallback IntelliSense
"""

import json
import platform
import shutil
from pathlib import Path
from typing import Dict, Any, List

from tools.base_tool import BaseTool
from tools.config import BuildConfig


class InitVSCodeTool(BaseTool):
    """Initialize VS Code workspace configuration."""
    
    @property
    def name(self) -> str:
        return "init-vscode"
    
    @property
    def category(self) -> str:
        return "setup"
    
    @property
    def description(self) -> str:
        return "Generate/update VS Code configuration for IntelliSense"
    
    @property
    def arguments(self):
        return []
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the init-vscode tool."""
        root_dir = self.get_root_dir()
        
        print("\n" + "=" * 70)
        print("Initializing VS Code Workspace")
        print("=" * 70)
        
        # Check if project is initialized
        build_config = BuildConfig(root_dir)
        if not build_config.exists():
            self.print_warning("Project not initialized. Run 'init' first.")
            print("Continuing with default configuration...")
            config = self._get_default_config()
        else:
            config = build_config.load()
        
        # Detect platform and compiler
        detected_platform = self._detect_platform()
        detected_compiler = self._detect_compiler()
        
        print(f"\n  Platform: {detected_platform}")
        print(f"  Compiler: {detected_compiler}")
        print(f"  Build Config: {config.get('config', 'release')}")
        print(f"  Architecture: {config.get('architecture', 'x86_64')}")
        print(f"  Precision: {config.get('precision', 'single')}")
        
        # Check dependencies
        deps_status = self._check_dependencies(root_dir)
        
        # Create .vscode directory
        vscode_dir = root_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        # Generate configuration files
        print()
        success = True
        
        if not self._generate_compile_commands(root_dir, config, detected_platform, detected_compiler, deps_status):
            success = False
        
        if not self._generate_settings_json(vscode_dir, root_dir):
            success = False
        
        if not self._generate_cpp_properties(vscode_dir, root_dir, config, detected_platform, detected_compiler, deps_status):
            success = False
        
        if success:
            print("\n" + "=" * 70)
            self.print_success("VS Code workspace initialized!")
            print("\nGenerated files:")
            print("  - compile_commands.json (in project root)")
            print("  - .vscode/settings.json")
            print("  - .vscode/c_cpp_properties.json")
            print("\nNext steps:")
            print("  1. Reload VS Code window (Ctrl+Shift+P → 'Developer: Reload Window')")
            print("  2. Wait for clangd to index (~30-60 seconds)")
            print("  3. Open a source file to verify IntelliSense")
            print("=" * 70)
            return 0
        else:
            print("\n" + "=" * 70)
            self.print_error("VS Code initialization completed with warnings")
            print("=" * 70)
            return 1
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "godot_version": "4.4",
            "platform": self._detect_platform(),
            "config": "release",
            "target": "editor",
            "architecture": "x86_64",
            "precision": "single",
            "jobs": 4,
        }
    
    def _detect_platform(self) -> str:
        """Detect current platform."""
        system = platform.system()
        if system == "Windows":
            return "windows"
        elif system == "Linux":
            return "linux"
        elif system == "Darwin":
            return "macos"
        return "unknown"
    
    def _detect_compiler(self) -> str:
        """Detect compiler."""
        system = platform.system()
        if system == "Windows":
            # Check if MSVC is available
            if shutil.which("cl"):
                return "msvc"
            elif shutil.which("g++"):
                return "gcc"
            elif shutil.which("clang++"):
                return "clang"
        elif system in ["Linux", "Darwin"]:
            if shutil.which("clang++"):
                return "clang"
            elif shutil.which("g++"):
                return "gcc"
        return "unknown"
    
    def _check_dependencies(self, root_dir: Path) -> Dict[str, bool]:
        """Check which dependencies are available."""
        status = {
            "godot_cpp": False,
            "godot_cpp_gen": False,
            "libgit2": False,
            "libhv": False,
            "nlohmann": False,
            "catch2": False,
        }
        
        # Check godot-cpp
        godot_cpp = root_dir / "third_party" / "godot-cpp"
        if godot_cpp.exists() and list(godot_cpp.iterdir()):
            status["godot_cpp"] = True
            # Check for generated headers
            gen_include = godot_cpp / "gen" / "include"
            if gen_include.exists():
                status["godot_cpp_gen"] = True
        
        # Check libgit2
        libgit2_inc = root_dir / "third_party" / "libgit2" / "include"
        libgit2_lib_dir = root_dir / "build_ext_libs"
        if libgit2_inc.exists():
            if platform.system() == "Windows":
                libgit2_lib = libgit2_lib_dir / "git2.lib"
            else:
                libgit2_lib = libgit2_lib_dir / "libgit2.a"
            status["libgit2"] = libgit2_lib.exists()
        
        # Check libhv
        libhv_inc = root_dir / "third_party" / "libhv" / "include"
        if libhv_inc.exists():
            if platform.system() == "Windows":
                libhv_lib = libgit2_lib_dir / "hv_static.lib"
            else:
                libhv_lib = libgit2_lib_dir / "libhv_static.a"
            status["libhv"] = libhv_lib.exists()
        
        # Check nlohmann/json
        nlohmann = root_dir / "third_party" / "nlohmann" / "include"
        status["nlohmann"] = nlohmann.exists()
        
        # Check catch2
        catch2 = root_dir / "third_party" / "catch2" / "src"
        status["catch2"] = catch2.exists()
        
        return status
    
    def _scan_source_files(self, root_dir: Path) -> List[Path]:
        """Scan for all C++ source files."""
        src_dir = root_dir / "src"
        if not src_dir.exists():
            return []
        
        sources = []
        for ext in ["*.cpp", "*.cc", "*.cxx"]:
            sources.extend(src_dir.rglob(ext))
        
        return sources
    
    def _generate_compile_commands(self, root_dir: Path, config: Dict[str, Any],
                                   detected_platform: str, compiler: str,
                                   deps_status: Dict[str, bool]) -> bool:
        """Generate compile_commands.json."""
        print("📝 Generating compile_commands.json...")
        
        # Get all source files
        sources = self._scan_source_files(root_dir)
        if not sources:
            self.print_warning("No source files found in src/")
            return True  # Non-fatal
        
        # Build include paths
        include_paths = self._get_include_paths(root_dir, deps_status)
        
        # Build defines
        defines = self._get_defines(config, detected_platform, deps_status)
        
        # Build compiler command
        compiler_path = self._get_compiler_path(compiler)
        
        # Generate compile commands
        commands = []
        for source in sources:
            rel_path = source.relative_to(root_dir)
            
            # Build command arguments
            args = [compiler_path]
            
            # Add standard
            args.append("-std=c++17")
            
            # Add includes
            for inc in include_paths:
                args.append(f"-I{inc}")
            
            # Add defines
            for define in defines:
                args.append(f"-D{define}")
            
            # Add source file
            args.append(str(rel_path))
            
            commands.append({
                "directory": str(root_dir),
                "command": " ".join(args),
                "file": str(rel_path),
            })
        
        # Write compile_commands.json
        output_file = root_dir / "compile_commands.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(commands, f, indent=2)
            self.print_success(f"Generated compile_commands.json ({len(commands)} files)")
            return True
        except Exception as e:
            self.print_error(f"Failed to write compile_commands.json: {e}")
            return False
    
    def _generate_settings_json(self, vscode_dir: Path, root_dir: Path) -> bool:
        """Generate or update settings.json."""
        print("📝 Generating .vscode/settings.json...")
        
        settings_file = vscode_dir / "settings.json"
        
        # Load existing settings
        existing = {}
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        
        # Add/update GodotAI-specific settings
        godotai_settings = {
            "clangd.arguments": [
                f"--compile-commands-dir={str(root_dir)}",
                "--background-index",
                "--clang-tidy",
                "--header-insertion=never",
                "--completion-style=detailed",
                "--function-arg-placeholders",
                "--fallback-style=llvm"
            ],
            "clangd.path": "clangd",
            "C_Cpp.intelliSenseEngine": "disabled",
            "files.associations": {
                "*.hpp": "cpp",
                "*.cpp": "cpp"
            },
            "C_Cpp.errorSquiggles": "disabled",
        }
        
        # Merge settings (preserve user settings)
        for key, value in godotai_settings.items():
            existing[key] = value
        
        # Write settings.json
        try:
            with open(settings_file, 'w') as f:
                json.dump(existing, f, indent=2)
            self.print_success("Generated .vscode/settings.json")
            return True
        except Exception as e:
            self.print_error(f"Failed to write settings.json: {e}")
            return False
    
    def _generate_cpp_properties(self, vscode_dir: Path, root_dir: Path,
                                config: Dict[str, Any], detected_platform: str,
                                compiler: str, deps_status: Dict[str, bool]) -> bool:
        """Generate c_cpp_properties.json."""
        print("📝 Generating .vscode/c_cpp_properties.json...")
        
        cpp_props_file = vscode_dir / "c_cpp_properties.json"
        
        # Load existing properties
        existing = {"configurations": [], "version": 4}
        if cpp_props_file.exists():
            try:
                with open(cpp_props_file, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        
        # Build include paths
        include_paths = [str(p) for p in self._get_include_paths(root_dir, deps_status)]
        
        # Build defines
        defines = self._get_defines(config, detected_platform, deps_status)
        
        # Get IntelliSense mode
        intellisense_mode = self._get_intellisense_mode(detected_platform, compiler)
        
        # Create GodotAI configuration
        godotai_config = {
            "name": "GodotAI",
            "includePath": include_paths,
            "defines": defines,
            "cStandard": "c17",
            "cppStandard": "c++17",
            "intelliSenseMode": intellisense_mode,
        }
        
        # Add compiler path if available
        compiler_path = self._get_compiler_path(compiler)
        if compiler_path != "c++":
            godotai_config["compilerPath"] = compiler_path
        
        # Remove existing GodotAI config
        existing["configurations"] = [c for c in existing["configurations"] if c.get("name") != "GodotAI"]
        
        # Add new GodotAI config
        existing["configurations"].insert(0, godotai_config)
        
        # Write c_cpp_properties.json
        try:
            with open(cpp_props_file, 'w') as f:
                json.dump(existing, f, indent=2)
            self.print_success("Generated .vscode/c_cpp_properties.json")
            return True
        except Exception as e:
            self.print_error(f"Failed to write c_cpp_properties.json: {e}")
            return False
    
    def _get_include_paths(self, root_dir: Path, deps_status: Dict[str, bool]) -> List[Path]:
        """Get all include paths."""
        paths = []
        
        # Source directory
        paths.append(root_dir / "src")
        
        # godot-cpp
        if deps_status["godot_cpp"]:
            paths.append(root_dir / "third_party" / "godot-cpp" / "gdextension")
            paths.append(root_dir / "third_party" / "godot-cpp" / "include")
            if deps_status["godot_cpp_gen"]:
                paths.append(root_dir / "third_party" / "godot-cpp" / "gen" / "include")
        
        # libgit2
        if deps_status["libgit2"]:
            paths.append(root_dir / "third_party" / "libgit2" / "include")
        
        # libhv
        if deps_status["libhv"]:
            paths.append(root_dir / "third_party" / "libhv" / "include")
        
        # nlohmann/json
        if deps_status["nlohmann"]:
            paths.append(root_dir / "third_party" / "nlohmann" / "include")
        
        # catch2
        if deps_status["catch2"]:
            paths.append(root_dir / "third_party" / "catch2" / "src")
        
        return paths
    
    def _get_defines(self, config: Dict[str, Any], detected_platform: str,
                    deps_status: Dict[str, bool]) -> List[str]:
        """Get all preprocessor defines."""
        defines = []
        
        # Platform defines
        if detected_platform == "windows":
            defines.extend(["_WIN32", "NOMINMAX", "GODOT_WINDOWS"])
        elif detected_platform == "linux":
            defines.extend(["__linux__", "GODOT_LINUXBSD"])
        elif detected_platform == "macos":
            defines.extend(["__APPLE__", "GODOT_MACOS"])
        
        # Build type defines
        target = config.get("target", "editor")
        if target == "editor":
            defines.append("TOOLS_ENABLED")
        
        build_config = config.get("config", "release")
        if build_config == "debug":
            defines.append("DEBUG_ENABLED")
        
        # Precision defines
        precision = config.get("precision", "single")
        if precision == "single":
            defines.append("REAL_T_IS_FLOAT")
        else:
            defines.append("REAL_T_IS_DOUBLE")
        
        # Dependency defines
        if deps_status["libgit2"]:
            defines.append("GODOTAI_HAS_LIBGIT2")
        
        if deps_status["libhv"]:
            defines.append("GODOTAI_HAS_LIBHV")
        
        return defines
    
    def _get_compiler_path(self, compiler: str) -> str:
        """Get compiler path."""
        if compiler == "msvc":
            cl_path = shutil.which("cl")
            return cl_path if cl_path else "cl"
        elif compiler == "gcc":
            return shutil.which("g++") or "g++"
        elif compiler == "clang":
            return shutil.which("clang++") or "clang++"
        return "c++"
    
    def _get_intellisense_mode(self, detected_platform: str, compiler: str) -> str:
        """Get IntelliSense mode."""
        if detected_platform == "windows":
            if compiler == "msvc":
                return "windows-msvc-x64"
            elif compiler == "gcc":
                return "windows-gcc-x64"
            else:
                return "windows-clang-x64"
        elif detected_platform == "linux":
            if compiler == "gcc":
                return "linux-gcc-x64"
            else:
                return "linux-clang-x64"
        elif detected_platform == "macos":
            return "macos-clang-x64"
        
        return "linux-gcc-x64"  # Fallback
