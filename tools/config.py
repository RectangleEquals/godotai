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
        "config": "release",
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
        self._config: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary (or defaults if file doesn't exist)
        """
        if self._config is not None:
            return self._config
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = json.load(f)
        else:
            self._config = self.DEFAULT_CONFIG.copy()
        
        return self._config
    
    def save(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
        """
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
        self.save(config)
    
    def exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_path.exists()
    
    def delete(self) -> None:
        """Delete configuration file."""
        if self.config_path.exists():
            self.config_path.unlink()
        self._config = None