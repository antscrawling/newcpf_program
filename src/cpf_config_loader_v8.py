import json
from datetime import datetime, date

DATE_KEYS = {"START_DATE", "END_DATE", "BIRTH_DATE"}
DATE_FORMAT = "%Y-%m-%d"

class ConfigLoader:
    
    def __init__(self, config_path):
        self.path = config_path
        self.config = self.load_config()
        
    def __getitem__(self, key):
        """Get item from the loaded config."""
        if not hasattr(self, 'config_data'):
            self.config_data = self.load_config()
        return self.config_data.get(key, None)

    def __setitem__(self, key, value):
        """Set item in the loaded config."""
        if not hasattr(self, 'config_data'):
            self.config_data = self.load_config()
        self.config_data[key] = value
        with open(self.path, 'w') as f:
            json.dump(self.config_data, f, indent=4)

    # Attribute-style access: cfg.key
    def __getattr__(self, name):
        if name in self._config_data:
            return self._config_data[name]
        raise AttributeError(f"'ConfigLoader' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Allow setting internal attrs like path and _config_data
        if name in {"path", "_config_data"}:
            super().__setattr__(name, value)
        else:
            self._config_data[name] = value
            self.save_config()
            
                        
    def save(self, output_path=None):
        serializable_data = {}
        for key, value in self.data.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = value.strftime(DATE_FORMAT)
            else:
                serializable_data[key] = value
        out_path = output_path or self.config_path
        with open(out_path, 'w') as f:
            json.dump(serializable_data, f, indent=4)
                
    def load_config(self):
        """Load JSON config from a file."""
        with open(self.config, 'r') as f:
            config = json.load(f)
        if isinstance(config, list):
            # Convert list to a dictionary with indices as keys
            config = {str(index): item for index, item in enumerate(config)}
        elif isinstance(config, dict):
        
            for key in DATE_KEYS:
                if key in config and isinstance(config[key], str):
                    try:
                        config[key] = datetime.strptime(config[key], DATE_FORMAT)
                    except ValueError:
                        raise ValueError(f"Date for {key} must be in format YYYY-MM-DD")
        return config

    def flatten_dict(self,d, parent_key="", sep="."):
        """
        Flattens a nested dictionary into a single-level dictionary with keys joined by `sep`.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def unflatten_dict(self,d, sep="."):
        """
        Converts a flattened dictionary with keys like 'a.b.c' back into a nested dictionary.
        """
        result = {}
        for k, v in d.items():
            keys = k.split(sep)
            current = result
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = v 
        return result
    