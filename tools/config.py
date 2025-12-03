"""
Configuration management for the build system.

Handles reading/writing .buildconfig.json and providing defaults.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class BuildConfig:
    """Manages build configuration."""
    
    CONFIG_FILE = ".buildconfig.json"
    
    DEFAULT_CONFIG = {
        "godot_version": "4.4",
        "platform": "windows",
        "target": "editor",  # Editor-only plugin
        "architecture": "x86_64",
        "jobs": 4,
    }
    
    def __init__(self, root_dir: Path):
        """
        Initialize configuration.
        
        Args:
            root_dir: Repository root directory
        """
        self.root_dir = root_dir
        self.config_path = root_dir / self.CONFIG_FILE
        self._config: Dict[str, Any] = {}
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary (or defaults if file doesn't exist)
        """
        if self._config:
            return self._config
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = json.load(f)
                
                # Migrate old config values
                if "config" in self._config:
                    # Old key, migrate to target
                    old_config = self._config.pop("config")
                    if old_config == "debug":
                        self._config["target"] = "editor"  # Debug builds are for editor
                    elif old_config == "release":
                        self._config["target"] = "editor"  # Still editor, just different optimization
                
                # Ensure target is always editor
                self._config["target"] = "editor"
        else:
            self._config = self.DEFAULT_CONFIG.copy()
        
        return self._config
    
    def save(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
        """
        # Ensure target is always editor
        config["target"] = "editor"
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        self._config = config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        config = self.load()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        config = self.load()
        config[key] = value
        
        # Ensure target is always editor
        if key == "target" or "target" not in config:
            config["target"] = "editor"
        
        self.save(config)
    
    def exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_path.exists()
    
    def delete(self) -> None:
        """Delete configuration file."""
        if self.config_path.exists():
            self.config_path.unlink()
        self._config = {}