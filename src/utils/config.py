"""Configuration management."""

import yaml
from pathlib import Path
from typing import Any, Dict

class Config:
    """Configuration manager."""
    
    def __init__(self, config_path: str = "config/default_config.yaml"):
        """Load configuration from YAML file."""
        self.config_path = Path(config_path)
        
        with open(self.config_path) as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Example: config.get("model.temperature") -> 0.7
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        """Return full configuration as dictionary."""
        return self._config.copy()
