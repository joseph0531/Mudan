import yaml
import os

def load_settings(file_name):
    """Load settings from settings_local.yaml or settings.yaml"""
    # Try to load local settings first, fall back to default settings
    settings_file = file_name if os.path.exists(file_name) else 'settings.yaml'
    
    try:
        with open(settings_file, 'r') as f:
            settings = yaml.safe_load(f)
        return settings
    except Exception as e:
        print(f"Warning: Could not load {settings_file}: {e}")
        return {} 