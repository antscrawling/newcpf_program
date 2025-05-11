import json
from datetime import datetime, date
import os


SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to the src directory
CONFIG_FILENAME = os.path.join(SRC_DIR, 'cpf_config.json')  # Full path to the config file
DATABASE_NAME = os.path.join(SRC_DIR, 'cpf_simulation.db')  # Full path to the database file

DATE_KEYS = {"START_DATE", "END_DATE", "BIRTH_DATE"}
DATE_FORMAT = "%Y-%m-%d"

class ConfigLoader:
    """
    Load config from JSON, converting date strings to datetime objects.
    Also supports saving the config back to JSON (round-trip).
    """
    def __init__(self, config_filename):
        # Dynamically determine the path to the src directory
        self.src_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(self.src_dir, config_filename)
        self._config_data = self._load_config()  # Initialize _config_data properly

    def _load_config(self):
        """
        Load the configuration file and parse its contents.
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Configuration file not found: {self.path}")
        try:
            with open(self.path, 'r') as myfile:
                # Read the entire file as JSON
                config_data = json.load(myfile)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")
        # Ensure the data is a dictionary
        if isinstance(config_data, list):
            # Convert list to a dictionary with indices as keys
            config_data = {str(index): item for index, item in enumerate(config_data)}
        elif not isinstance(config_data, dict):
            raise ValueError(f"Invalid configuration format: Expected a dictionary, got {type(config_data)}")
        return config_data

    def save(self, output_filename=None):
        """Save the configuration to a file."""
        serializable_data = {}
        for key, value in self._config_data.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = value.strftime(DATE_FORMAT)
            else:
                serializable_data[key] = value
        # Save to the src directory
        output_path = os.path.join(self.src_dir, output_filename or os.path.basename(self.path))
        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=4)

    def flatten_dict(self, d, parent_key="", sep="."):
        """Flatten a nested dictionary into a single-level dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def unflatten_dict(self, d, sep="."):
        """Convert a flattened dictionary into a nested dictionary."""
        result = {}
        for k, v in d.items():
            keys = k.split(sep)
            current = result
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = v
        return result

if __name__ == "__main__":
    # Load the configuration file from the src directory
    my_config = ConfigLoader('cpf_config.json')
    flattened_config = my_config.flatten_dict(my_config._config_data)
    
    print(flattened_config)

    # Save the configuration back to the src directory
    my_config.save('cpf_config_updated.json')