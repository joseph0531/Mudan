#!/usr/bin/env python3
"""
Settings Editing History Manager
Tracks and logs all settings changes with timestamps using YAML multi-document format
"""

import yaml
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.logging_helper import set_logger
from utils.settings_loader import load_settings
from utils.editable_params import editable_params_list

class SettingsEditingManager:
    """Manages settings editing history using YAML multi-document format for efficient append-only logging"""
    
    def __init__(self, settings_file: str = 'settings_local.yaml', history_file: str = 'settings_local_edit_history.yaml'):
        """
        Initialize the settings editing manager.
        
        Args:
            settings_file: Path to the main settings file
            history_file: Path to the history file (YAML multi-document format)
        """
        self.settings_file = settings_file
        self.settings = self.get_settings()
        self.history_file = history_file
        self.logger = set_logger('SettingsEditingManager')
        self.editable_params_list = editable_params_list
        
        # Ensure history file exists with header
        self._ensure_history_file()

    def get_settings(self):
        return load_settings(self.settings_file)
    
    def _ensure_history_file(self):
        """Ensure the history file exists with proper header"""
        if not os.path.exists(self.history_file):
            header = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "settings_file": self.settings_file,
                "description": "Settings edit history log (YAML multi-document format)"
            }
            with open(self.history_file, 'w') as f:
                yaml.dump(header, f, default_flow_style=False, sort_keys=False)
                f.write("---\n")  # Document separator
            self.logger.info(f"Created new history file: {self.history_file}")
    
    def record_edit(self, param_name: str, old_value: Any, new_value: Any, 
                   user: str = "unknown", source: str = "unknown") -> bool:
        """
        Record a settings edit by appending a new YAML document to the history file.
        This is extremely efficient as it only appends to the end of the file.
        
        Args:
            param_name: Name of the parameter being edited
            old_value: Previous value of the parameter
            new_value: New value of the parameter
            user: User who made the change (optional)
            source: Source of the change (e.g., 'remote', 'local', 'api') (optional)
            
        Returns:
            bool: True if successfully recorded, False otherwise
        """
        try:
            edit_record = {
                "timestamp": datetime.now().isoformat(),
                "param_name": param_name,
                "old_value": old_value,
                "new_value": new_value,
                "user": user,
                "source": source,
                "settings_file": self.settings_file
            }
            
            # Simply append the new document to the file
            with open(self.history_file, 'a') as f:
                yaml.dump(edit_record, f, default_flow_style=False, sort_keys=False)
                f.write("---\n")  # Document separator
            
            self.logger.info(f"Recorded edit: {param_name} = {old_value} -> {new_value} (by {user} via {source})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record edit: {e}")
            return False
        
    def clear_history(self) -> bool:
        """
        Clear all edit history by recreating the file with just the header.
        
        Returns:
            bool: True if successfully cleared, False otherwise
        """
        try:
            header = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "settings_file": self.settings_file,
                "description": "Settings edit history log (YAML multi-document format)"
            }
            with open(self.history_file, 'w') as f:
                yaml.dump(header, f, default_flow_style=False, sort_keys=False)
                f.write("---\n")  # Document separator
            self.logger.info("Cleared edit history")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear history: {e}")
            return False
    
    def backup_current_settings(self, backup_file: str = None) -> bool:
        """
        Create a backup of the current settings file.
        
        Args:
            backup_file: Backup file path (optional)
            
        Returns:
            bool: True if successfully backed up, False otherwise
        """
        try:
            if backup_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{self.settings_file}.backup_{timestamp}"
            
            if os.path.exists(self.settings_file):
                import shutil
                shutil.copy2(self.settings_file, backup_file)
                self.logger.info(f"Backed up settings to: {backup_file}")
                return True
            else:
                self.logger.warning(f"Settings file not found: {self.settings_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to backup settings: {e}")
            return False
    
    def save_settings(self, settings: dict):
        """Save the settings to the settings file"""
        with open(self.settings_file, 'w') as f:
            yaml.dump(settings, f, default_flow_style=False, sort_keys=False)

    def get_editable_current_settings(self) -> dict:
        """Get the current settings"""
        settings_dict = {}  
        self.settings = self.get_settings()
        for param in self.editable_params_list:
            param['value'] = self.get_parameter_value(self.settings, param['path'])
            settings_dict[param['name']] = param['value']
        return settings_dict
    
    def get_parameter_value(self, settings: dict, path: list):
        """Get parameter value from settings using path"""
        current = settings
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def get_parameter_info(self, param_name: str):
        """Get parameter info from editable_params_list"""
        for param in self.editable_params_list:
            if param['name'] == param_name:
                return param
        return None
    
    def set_parameter_value(self, settings: dict, path: list, value):
        """Set parameter value in settings using path"""
        current = settings
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def parse_parameter_value(self, param_name: str, value_str: str):
        """Parse parameter value based on parameter type"""
        try:
            param_info = None
            for param in self.editable_params_list:
                if param['name'] == param_name:
                    param_info = param
                    break
            
            if not param_info:
                raise ValueError(f"Unknown parameter: {param_name}")
            
            param_type = param_info['type']
            
            if param_type == 'int':
                return int(value_str)
            elif param_type == 'float':
                return float(value_str)
            elif param_type == 'bool':
                if value_str.lower() in ['true', '1', 'yes']:
                    return True
                elif value_str.lower() in ['false', '0', 'no']:
                    return False
                else:
                    raise ValueError(f"Invalid boolean value: {value_str}")
            elif param_type == 'string':
                return value_str
            elif param_type == 'list_float':
                # Handle list format like [1.0, 2.0, 3.0] or "1.0,2.0,3.0"
                if value_str.startswith('[') and value_str.endswith(']'):
                    value_str = value_str[1:-1]
                values = [float(x.strip()) for x in value_str.split(',') if x.strip()]
                return values
            else:
                # Default to string
                return value_str
        except Exception as e:
            raise ValueError(f"Failed to parse value '{value_str}' for parameter '{param_name}': {e}")

