import json
from datetime import datetime, date
import os
from typing import Any  # Import Any for type hinting
import re
from dateutil.relativedelta import relativedelta

DATE_FORMAT = "%Y-%m-%d"


class ConfigLoader:
    """
    Load config from JSON, converting date strings to datetime objects.
    Also supports saving the config back to JSON (round-trip).
    """
    def __init__(self, config_path):
        # Resolve the absolute path of the configuration file
        self.config_path = os.path.abspath(config_path)
        self.data = None
        self._load_config()

    def _load_config(self):
        """
        Load the configuration file and parse its contents.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r') as myfile:
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

        # Convert date strings to date objects
        for key, value in config_data.items():
            if isinstance(value, str):
                try:
                    config_data[key] = datetime.strptime(value, DATE_FORMAT).date()
                except ValueError:
                    pass  # Not a date-formatted string

        self.data = config_data

    def save(self, output_path=None):
        """Save current config data back to JSON (converting datetime to string)."""
        serializable_data = {}
        for key, value in self.data.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = value.strftime(DATE_FORMAT)
            else:
                serializable_data[key] = value
        out_path = output_path or self.config_path
        with open(out_path, 'w') as f:
            json.dump(serializable_data, f, indent=4)

    def getdata(self, keys, default=None) -> Any:
        """
        Retrieve a value from the configuration using a single key or a list of keys.
        :param keys: A single key (str) or a list of keys (list of str).
        :param default: Default value to return if the key(s) are not found.
        :return: The value associated with the key(s) or the default value.
        """
        if isinstance(keys, str):
            keys = [keys]  # Convert single key to a list for uniform processing

        current_value = self.data
        for key in keys:
            if isinstance(current_value, dict):
                current_value = current_value.get(key, default)
            else:
                return default
        return current_value

    def get_keys_and_values(self):
        """
        Extract all keys and values from the configuration as two separate lists.
        :return: A tuple containing two lists - keys and values.
        """
        keys = []
        values = []

        def extract(data, parent_key=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{parent_key}.{key}" if parent_key else key
                    keys.append(full_key)
                    if isinstance(value, (dict, list)):
                        extract(value, full_key)
                    else:
                        values.append(value)
            elif isinstance(data, list):
                for index, item in enumerate(data):
                    full_key = f"{parent_key}[{index}]"
                    keys.append(full_key)
                    if isinstance(item, (dict, list)):
                        extract(item, full_key)
                    else:
                        values.append(item)

        extract(self.data)
        return keys, values


# Example usage
if __name__ == "__main__":
    try:
        # Load the configuration
        config_loader = ConfigLoader('cpf_logs_updated.json')
        print(config_loader.data)
    except FileNotFoundError:
        # Create a dummy config for testing if it doesn't exist
        dummy = [
            {"key1": "value1"},
            {"key2": "value2"},
            {"key3": "value3"}
        ]
        with open('cpf_logs_updated.json', 'w') as f:
            json.dump(dummy, f, indent=4)
        config_loader = ConfigLoader('cpf_logs_updated.json')
        print(config_loader.data)