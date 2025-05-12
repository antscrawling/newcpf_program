import json
from datetime import datetime, date
import os
from typing import Any
import re   
from pprint import pprint


SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to the src directory
CONFIG_FILENAME = os.path.join(SRC_DIR, 'cpf_config.json')  # Full path to the config file
CONFIG_FILENAME_FOR_USE = os.path.join(SRC_DIR, 'cpf_config_for_use.json')  # Full path to the config file for use
DATABASE_NAME = os.path.join(SRC_DIR, 'cpf_simulation.db')  # Full path to the database file

DATE_FORMAT = "%Y-%m-%d"

def custom_serializer(obj):
    """Custom serializer for non-serializable objects like datetime."""
    if isinstance(obj, (datetime,date)):
        return obj.strftime(DATE_FORMAT)
    raise TypeError(f"Type {type(obj)} not serializable")

class ConfigLoader:
    """
    Load config from JSON, converting date strings to datetime objects.
    Also supports saving the config back to JSON (round-trip).
    Includes features for flattening/unflattening dictionaries, resolving formulas, and retrieving nested values.
    """

    def __init__(self, config_filename: str = None):
        self.src_dir = SRC_DIR
        self.path = os.path.join(SRC_DIR, config_filename)  # Full path to the config fileconfig_filename
        self.data = None
        self._load_config()
        #self._duplicate_config()

    def _load_config(self):
        """
        Load the configuration file and parse its contents.
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Configuration file not found: {self.path}")
        try:
            with open(self.path, 'r') as myfile:
                config_data = json.load(myfile)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

        # Ensure the data is a dictionary
        if isinstance(config_data, list):
            config_data = {str(index): item for index, item in enumerate(config_data)}
        elif not isinstance(config_data, dict):
            raise ValueError(f"Invalid configuration format: Expected a dictionary, got {type(config_data)}")
        self.data = config_data
        
    def _duplicate_config(self):
        """
        Create a duplicate of the configuration file for use.
        """
        serializable_data = {}
        for key, value in self.data.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = custom_serializer(value)
            else:
                serializable_data[key] = value
        with open(CONFIG_FILENAME_FOR_USE, 'w') as outfile:
            json.dump(self.data, outfile, indent=4, default=custom_serializer)
                                                                       
    def save(self, output_filename=None):
        """Save the configuration to a file."""
        serializable_data = {}
        for key, value in self._config_data.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = value.strftime(DATE_FORMAT)
            else:
                serializable_data[key] = value
        # Save to the src directory
        output_path = os.path.join(SRC_DIR, output_filename or os)
        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=4)
            
    def save_file(self,infile: str, outfile=None):
        """
        Save the configuration to a file.
        """
        serializable_data = {}
        for key, value in infile.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = value.strftime(DATE_FORMAT)
            else:
                serializable_data[key] = value

       # output_path = os.path.join(self.src_dir, output_filename or os.path.basename(self.path))
        with open(outfile, 'w') as f:
            json.dump(serializable_data, f, indent=4,default=custom_serializer)

    def getdata(self, keys=None, default=None) -> Any:
        """
        Retrieve a value from the configuration using a single key, a list of keys, or return the entire configuration if no keys are provided.
        """
        # If no keys are provided, return the entire configuration
        if keys is None:
            return self.data

        # If a single key is provided as a string, convert it to a list
        if isinstance(keys, str):
            keys = [keys]

        current_value = self.data
        # If keys is a list, tuple, or set, traverse the nested dictionary
        if isinstance(keys, (list, tuple, set)):
            for key in keys:
                if isinstance(current_value, dict):
                    current_value = current_value.get(key, default)
                else:
                    return default
        return current_value

    def flatten_dict(self, d, parent_key="", sep="."):
        """
        Flatten a nested dictionary into a single-level dictionary.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def unflatten_dict(self, d, sep="."):
        """
        Convert a flattened dictionary into a nested dictionary.
        """
        result = {}
        for k, v in d.items():
            keys = k.split(sep)
            current = result
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = v
        return result

    def resolve_formulas(self):
        """
        Resolve formulas in the configuration data by evaluating them dynamically.
        """
        def evaluate_formula(formula, context):
            """
            Evaluate a formula string using the provided context (dictionary of values).
            """
            try:
                return eval(formula, {}, context)
            except Exception as e:
                raise ValueError(f"Error evaluating formula '{formula}': {e}")

        flat_config = self.flatten_dict(self.data)

        for key, value in flat_config.items():
            if isinstance(value, dict) and 'formula' in value:
                formula = value['formula']
                try:
                    result = evaluate_formula(formula, flat_config)
                    value['amount'] = result
                except ValueError as e:
                    print(f"Failed to resolve formula for key '{key}': {e}")

        self.data = self.unflatten_dict(flat_config)

    def get_keys_and_values(self):
        """
        Extract all keys and values from the configuration as two separate lists.
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

    def get_nested_value(self, nested, dotted_key):
        """
        Retrieve a value from a nested dictionary using a dotted key.
        """
        if not isinstance(nested, dict):
            raise TypeError("The first argument must be a dictionary.")
        if not isinstance(dotted_key, str):
            raise TypeError("The second argument must be a string.")
        keys = dotted_key.split(".")
        for key in keys:
            if isinstance(nested, dict) and key in nested:
                nested = nested[key]
            else:
                return None
        return nested


if __name__ == "__main__":
    # Initialize the ConfigLoader
    config_loader = ConfigLoader(config_filename='test_config1.json')

    # Retrieve the entire configuration
   #entire_config = config_loader.getdata()
   #pprint(entire_config)

    # Retrieve a specific value
    specific_value = config_loader.getdata(keys=["oa_allocation_below_55", "allocation"])
    pprint( specific_value)
