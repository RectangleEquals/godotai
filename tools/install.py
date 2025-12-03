"""
Plugin installation tool.

Installs the built GodotAI plugin into a Godot project with the correct
directory structure: addons/gdai/
"""

import shutil
from pathlib import Path
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolArgument


class InstallTool(BaseTool):
    """Install GodotAI plugin to a Godot project."""
    
    @property
    def name(self) -> str:
        return "install"
    
    @property
    def description(self) -> str:
        return "Install GodotAI plugin into a Godot project"
    
    @property
    def category(self) -> str:
        return "install"
    
    @property
    def arguments(self):
        return [
            ToolArgument(
                name="project_path",
                description="Path to Godot project (leave empty for prompt)",
                type=str,
                required=False,
                default=""
            ),
            ToolArgument(
                name="create_scaffold",
                description="Create project scaffold if path doesn't exist",
                type=bool,
                required=False,
                default=True
            ),
        ]
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the install tool."""
        root_dir = self.get_root_dir()
        
        # Get project path
        project_path = args.get("project_path", "").strip()
        create_scaffold = args.get("create_scaffold", True)
        
        if not project_path:
            project_path = self._prompt_for_project_path()
            if not project_path:
                self.print_error("Installation cancelled")
                return 1
        
        project_dir = Path(project_path).resolve()
        
        print("\n" + "=" * 70)
        print("Installing GodotAI Plugin")
        print("=" * 70)
        print(f"\n  Project: {project_dir}")
        print(f"  Create scaffold: {create_scaffold}")
        print()
        
        # Check if plugin is built
        plugin_source = root_dir / "plugin"
        if not plugin_source.exists():
            self.print_error("Plugin not built. Run 'build' first.")
            return 1
        
        plugin_bin = plugin_source / "bin"
        if not plugin_bin.exists() or not any(plugin_bin.iterdir()):
            self.print_error("Plugin binaries not found. Run 'build' first.")
            return 1
        
        # Handle project directory
        if not project_dir.exists():
            if not create_scaffold:
                self.print_error(f"Project directory does not exist: {project_dir}")
                return 1
            
            print(f"📁 Creating project directory...")
            if not self._create_project_scaffold(project_dir):
                return 1
        
        # Create addon directory structure
        addon_dir = project_dir / "addons" / "gdai"
        
        if addon_dir.exists():
            response = input(f"\n⚠️  Addon directory already exists. Overwrite? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Installation cancelled")
                return 0
            
            print("🗑️  Removing existing addon...")
            shutil.rmtree(addon_dir)
        
        # Install the plugin
        if not self._install_plugin(plugin_source, addon_dir):
            return 1
        
        # Show summary
        self._show_install_summary(addon_dir)
        
        print("\n" + "=" * 70)
        self.print_success("GodotAI installed successfully!")
        print("=" * 70)
        print("\n💡 Next steps:")
        print(f"  1. Open the project in Godot: {project_dir}")
        print("  2. Go to: Project → Project Settings → Plugins")
        print("  3. Enable 'GodotAI'")
        print("  4. Look for the GodotAI menu in the editor toolbar")
        print()
        
        return 0
    
    def _prompt_for_project_path(self) -> str:
        """
        Prompt user for Godot project path.
        
        Returns:
            Project path or empty string if cancelled
        """
        print("\n" + "=" * 70)
        print("Godot Project Location")
        print("=" * 70)
        print("\nEnter the path to your Godot project.")
        print("If the directory doesn't exist, a minimal project scaffold will be created.")
        print("\nExamples:")
        print("  C:\\Users\\YourName\\Documents\\MyGame")
        print("  /home/user/projects/my-game")
        print("  ~/Documents/godot-projects/test-project")
        print()
        
        while True:
            path = input("Project path (or 'q' to quit): ").strip()
            
            if path.lower() == 'q':
                return ""
            
            if not path:
                print("❌ Path cannot be empty")
                continue
            
            # Expand user home directory
            path = Path(path).expanduser()
            
            return str(path)
    
    def _create_project_scaffold(self, project_dir: Path) -> bool:
        """
        Create minimal Godot project scaffold.
        
        Args:
            project_dir: Project directory to create
            
        Returns:
            True if successful
        """
        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create project.godot file
            project_godot = project_dir / "project.godot"
            if not project_godot.exists():
                project_godot.write_text(
                    "; Engine configuration file.\n"
                    "; It's best edited using the editor UI and not directly,\n"
                    "; since the parameters that go here are not all obvious.\n"
                    ";\n"
                    "; Format:\n"
                    ";   [section] ; section goes between []\n"
                    ";   param=value ; assign values to parameters\n"
                    "\n"
                    "config_version=5\n"
                    "\n"
                    "[application]\n"
                    "\n"
                    'config/name="GodotAI Test Project"\n'
                    'config/features=PackedStringArray("4.4")\n'
                )
                print(f"✓ Created project.godot")
            
            # Create addons directory
            addons_dir = project_dir / "addons"
            addons_dir.mkdir(exist_ok=True)
            print(f"✓ Created addons/ directory")
            
            self.print_success("Project scaffold created")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to create project scaffold: {e}")
            return False
    
    def _install_plugin(self, source_dir: Path, target_dir: Path) -> bool:
        """
        Install plugin files to target directory.
        
        Args:
            source_dir: Source plugin/ directory
            target_dir: Target addons/gdai/ directory
            
        Returns:
            True if successful
        """
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            config = self.get_tool_config()
            
            # Copy individual files
            files_to_copy = config.get("files_to_copy", ["gdai.gdextension", "plugin.cfg", "plugin.gd"])
            
            for filename in files_to_copy:
                src_file = source_dir / filename
                if src_file.exists():
                    shutil.copy2(src_file, target_dir / filename)
                    print(f"✓ Copied {filename}")
                else:
                    self.print_warning(f"Source file not found: {filename}")
            
            # Copy directories
            dirs_to_copy = config.get("directories_to_copy", ["bin", "plugin"])
            platform_subdirs = config.get("platform_subdirs", True)
            
            for dirname in dirs_to_copy:
                src_dir = source_dir / dirname
                if src_dir.exists():
                    target_subdir = target_dir / dirname
                    
                    # Remove existing directory
                    if target_subdir.exists():
                        shutil.rmtree(target_subdir)
                    
                    # Copy directory
                    shutil.copytree(src_dir, target_subdir)
                    print(f"✓ Copied {dirname}/ directory")
                    
                    # Count files
                    file_count = sum(1 for _ in target_subdir.rglob('*') if _.is_file())
                    print(f"  ({file_count} files)")
                else:
                    self.print_warning(f"Source directory not found: {dirname}/")
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to install plugin: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _show_install_summary(self, addon_dir: Path):
        """
        Show installation summary.
        
        Args:
            addon_dir: Installed addon directory
        """
        print("\n" + "=" * 70)
        print("Installation Summary")
        print("=" * 70)
        
        # Show directory structure
        print("\n📁 Installed structure:")
        self._print_tree(addon_dir, prefix="", max_depth=3)
        
        # Show library files
        bin_dir = addon_dir / "bin"
        if bin_dir.exists():
            print("\n📦 Installed libraries:")
            for platform_dir in sorted(bin_dir.iterdir()):
                if platform_dir.is_dir():
                    for lib_file in sorted(platform_dir.iterdir()):
                        if lib_file.is_file():
                            size_mb = lib_file.stat().st_size / (1024 * 1024)
                            print(f"  {platform_dir.name}/{lib_file.name} ({size_mb:.2f} MB)")
    
    def _print_tree(self, directory: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        """
        Print directory tree.
        
        Args:
            directory: Directory to print
            prefix: Prefix for tree lines
            max_depth: Maximum depth to print
            current_depth: Current depth level
        """
        if current_depth >= max_depth:
            return
        
        try:
            entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                
                if is_last:
                    print(f"{prefix}└── {entry.name}")
                    new_prefix = prefix + "    "
                else:
                    print(f"{prefix}├── {entry.name}")
                    new_prefix = prefix + "│   "
                
                if entry.is_dir():
                    self._print_tree(entry, new_prefix, max_depth, current_depth + 1)
        except PermissionError:
            pass