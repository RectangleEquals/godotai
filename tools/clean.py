"""
Clean tool.

Removes build artifacts, intermediate files, and optionally configuration.
Uses tools/config.json to determine what to clean.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List

from tools.base_tool import BaseTool, ToolArgument


class CleanTool(BaseTool):
    """Clean build artifacts and configuration."""
    
    @property
    def name(self) -> str:
        return "clean"
    
    @property
    def description(self) -> str:
        return "Clean build artifacts and optionally configuration"
    
    @property
    def category(self) -> str:
        return "clean"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="target",
                description="What to clean",
                type=str,
                required=False,
                default="build",
                choices=["build", "dependencies", "plugin", "config", "all"]
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the clean tool."""
        root_dir = self.get_root_dir()
        target = args.get("target", "build")
        
        print("\n" + "=" * 70)
        print("Cleaning Build Artifacts")
        print("=" * 70)
        print(f"\n  Target: {target}")
        print()
        
        # Get clean configuration
        config = self.get_tool_config()
        targets = config.get("targets", {})
        
        if target not in targets:
            self.print_error(f"Unknown clean target: {target}")
            print(f"\nAvailable targets: {', '.join(targets.keys())}")
            return 1
        
        # Confirm if cleaning config or all
        if target in ["config", "all"]:
            response = input(f"⚠️  This will remove configuration. Continue? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Clean cancelled")
                return 0
        
        # Get paths to clean
        patterns = targets[target]
        
        if not isinstance(patterns, list):
            patterns = [patterns]
        
        # Clean each pattern
        cleaned_count = 0
        for pattern in patterns:
            cleaned_count += self._clean_pattern(root_dir, pattern)
        
        # Summary
        print("\n" + "=" * 70)
        if cleaned_count > 0:
            self.print_success(f"Cleaned {cleaned_count} item(s)")
        else:
            self.print_info("Nothing to clean")
        print("=" * 70)
        
        return 0
    
    def _clean_pattern(self, root_dir: Path, pattern: str) -> int:
        """
        Clean files/directories matching a pattern.
        
        Args:
            root_dir: Repository root directory
            pattern: Path pattern to clean (supports wildcards)
            
        Returns:
            Number of items cleaned
        """
        cleaned = 0
        
        # Handle glob patterns
        if '*' in pattern:
            # Split pattern into parts
            parts = Path(pattern).parts
            base_parts = []
            glob_parts = []
            found_wildcard = False
            
            for part in parts:
                if '*' in part or found_wildcard:
                    glob_parts.append(part)
                    found_wildcard = True
                else:
                    base_parts.append(part)
            
            if base_parts:
                base_dir = root_dir / Path(*base_parts)
            else:
                base_dir = root_dir
            
            glob_pattern = str(Path(*glob_parts)) if glob_parts else '*'
            
            if not base_dir.exists():
                return 0
            
            # Find matching paths
            for path in base_dir.glob(glob_pattern):
                if path.exists():
                    if self._remove_path(path):
                        cleaned += 1
        else:
            # Direct path
            path = root_dir / pattern
            if path.exists():
                if self._remove_path(path):
                    cleaned += 1
        
        return cleaned
    
    def _remove_path(self, path: Path) -> bool:
        """
        Remove a file or directory.
        
        Args:
            path: Path to remove
            
        Returns:
            True if removed successfully
        """
        try:
            if path.is_dir():
                # Calculate size before removing
                size = self._calculate_dir_size(path)
                size_mb = size / (1024 * 1024)
                
                print(f"🗑️  Removing {path.name}/ ({size_mb:.1f} MB)...")
                shutil.rmtree(path)
            else:
                size = path.stat().st_size
                size_kb = size / 1024
                
                print(f"🗑️  Removing {path.name} ({size_kb:.1f} KB)...")
                path.unlink()
            
            return True
            
        except Exception as e:
            self.print_warning(f"Failed to remove {path}: {e}")
            return False
    
    def _calculate_dir_size(self, directory: Path) -> int:
        """
        Calculate total size of directory.
        
        Args:
            directory: Directory to calculate
            
        Returns:
            Total size in bytes
        """
        total = 0
        try:
            for entry in directory.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except:
            pass
        return total
    
    def clean_specific_paths(self, paths: List[str]) -> int:
        """
        Clean specific paths. Can be called by other tools.
        
        Args:
            paths: List of paths to clean (relative to repo root)
            
        Returns:
            Number of items cleaned
        """
        root_dir = self.get_root_dir()
        cleaned = 0
        
        for path_str in paths:
            path = root_dir / path_str
            if path.exists():
                if self._remove_path(path):
                    cleaned += 1
        
        return cleaned