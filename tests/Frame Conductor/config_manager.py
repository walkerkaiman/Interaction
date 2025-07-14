#!/usr/bin/env python3
"""
Configuration Manager for Frame Conductor

Handles loading and saving of application configuration to JSON files.
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration loading and saving."""
    
    def __init__(self, config_file: str = "sacn_sender_config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = config_file
        self.default_config = {
            'target_frame': 1000,
            'frame_rate': 30
        }
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary with loaded values or defaults
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            
        # Return defaults if loading fails
        return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration values.
        
        Args:
            config (Dict[str, Any]): Configuration to validate
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            target_frame = config.get('target_frame', 0)
            frame_rate = config.get('frame_rate', 0)
            
            # Validate target frame
            if not isinstance(target_frame, int) or target_frame < 0 or target_frame > 65535:
                return False
                
            # Validate frame rate
            if not isinstance(frame_rate, int) or frame_rate <= 0 or frame_rate > 120:
                return False
                
            return True
            
        except Exception:
            return False 