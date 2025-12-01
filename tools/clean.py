"""
Clean tool.

Removes build artifacts and optionally configuration files.
"""

import shutil
from pathlib import Path
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolArgument
from tools.config import BuildConfig


class CleanTool(BaseTool):
    """Clean build artifacts."""
    
    @property
    def name(self) -> str:
        return "clean"
    
    @property
    def description(self) -> str:
        return "Clean build artifacts and optionally configuration"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="target",
                description="What to clean",
                type=str,
                required=False,
                default="build",
                choices=["build", "config", "all", "everything"]
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the clean tool."""
        root_dir = self.get_root_dir()
        target = args.get("target", "build")
        
        print("\n" + "=" * 70)
        print("Cleaning GodotAI Project")
        print("=" * 70)
        print(f"\nTarget: {target}\n")
        
        cleaned_items = []
        
        # Clean build directory
        if target in ["build", "all", "everything"]:
            cleaned_items.extend(self._clean_build_artifacts(root_dir))
        
        # Clean configuration
        if target in ["config", "all", "everything"]:
            cleaned_items.extend(self._clean_config(root_dir))
        
        # Clean everything (including IDE files)
        if target == "everything":
            cleaned_items.extend(self._clean_ide_files(root_dir))
        
        # Show results
        print()
        if cleaned_items:
            self.print_success(f"Cleaned {len(cleaned_items)} items")
            
            # Show summary (first 10 items)
            print("\nCleaned:")
            for item in cleaned_items[:10]:
                print(f"  🗑️  {item}")
            
            if len(cleaned_items) > 10:
                print(f"  ... and {len(cleaned_items) - 10} more")
        else:
            self.print_info("Nothing to clean")
        
        print("\n" + "=" * 70)
        return 0
    
    def _clean_build_artifacts(self, root_dir: Path) -> list[str]:
        """Clean build artifacts."""
        cleaned = []
        
        # Build directory
        build_dir = root_dir / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            cleaned.append("build/")
        
        # External libraries
        ext_libs_dir = root_dir / "build_ext_libs"
        if ext_libs_dir.exists():
            shutil.rmtree(ext_libs_dir)
            cleaned.append("build_ext_libs/")
        
        # SCons files
        scons_files = [
            ".sconsign.dblite",
            ".sconf_temp",
            "config.log"
        ]
        for file in scons_files:
            file_path = root_dir / file
            if file_path.exists():
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                cleaned.append(file)
        
        # Object files in godot-cpp
        godot_cpp_dir = root_dir / "third_party" / "godot-cpp"
        if godot_cpp_dir.exists():
            for pattern in ["*.o", "*.obj", "*.a", "*.lib", "*.os"]:
                for file in godot_cpp_dir.rglob(pattern):
                    file.unlink()
                    cleaned.append(str(file.relative_to(root_dir)))
        
        return cleaned
    
    def _clean_config(self, root_dir: Path) -> list[str]:
        """Clean configuration files."""
        cleaned = []
        
        config = BuildConfig(root_dir)
        if config.exists():
            config.delete()
            cleaned.append(".buildconfig.json")
        
        return cleaned
    
    def _clean_ide_files(self, root_dir: Path) -> list[str]:
        """Clean IDE-generated files."""
        cleaned = []
        
        # compile_commands.json
        compile_commands = root_dir / "compile_commands.json"
        if compile_commands.exists():
            compile_commands.unlink()
            cleaned.append("compile_commands.json")
        
        # Python cache
        for pycache in root_dir.rglob("__pycache__"):
            shutil.rmtree(pycache)
            cleaned.append(str(pycache.relative_to(root_dir)))
        
        for pyc in root_dir.rglob("*.pyc"):
            pyc.unlink()
            cleaned.append(str(pyc.relative_to(root_dir)))
        
        return cleaned