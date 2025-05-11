import json
from datetime import datetime, date
import os
from typing import Any


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
    def __init__(self, config_filename: str =CONFIG_FILENAME):
        # Dynamically determine the path to the src directory
        self.src_dir = SRC_DIR
        self.path = CONFIG_FILENAME
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

    def getdata(self, keys):
        """
        Retrieve data from the configuration using a list of keys.
        The keys can be nested, e.g., ['key1', 'key2', 'key3'].
        """
        if isinstance(keys, str):
            keys = [keys]
        elif isinstance(keys, (list,tuple,set)):
            keys = keys
        data = self._config_data
        for key in keys:
            if isinstance(key, list):
                for k in key:
                    data = data[k]
            else:
                data = data[key]
        return data
    
    def save(self, output_filename=None):
        """Save the configuration to a file."""
        
        output = os.path.join(SRC_DIR, output_filename or os.path.basename(self.path))
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
    
    def calculate_fields_from_config(self):
        """
        Calculate fields based on the configuration.
        when the value has a key 'formula', parse the value
        """
        
        # identify any key == to 'formula'
        for key, value in self._config_data.items():
            if isinstance(value, dict) and 'formula' in value:
                # Parse the formula
                formula = value['formula']
                # Evaluate the formula (this is a placeholder, actual implementation may vary)
                # split between spaces

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
    
                    
                
                
                
                
                
        
        
        
        
  
  
        

if __name__ == "__main__":
        
    myconfig = {"salary_cap": 7400,
    "cpf_contribution_rates": {
        "below_55": {
            "employee": 0.2,
            "employer": 0.17,
            "total_contribution": {
                "formula": "{employee} * {salary_cap} + {employer} * {salary_cap}",
                "amount": 2778
                    }
                }
            } ,

               "salary_cap": 7400,
            "cpf_contribution_rates": {
                "below_55": {
                    "employee": 0.2,
                    "employer": 0.17,
                    "total_contribution": {
                        "formula": "employee * salary_cap + employer * salary_cap",
                        "amount": 2778
                    }
                }
            },
            "55_to_60": {
                "employee": 0.15,
                "employer": 0.14,
                "total_contribution": {
                    "formula": "employee * salary_cap + employer * salary_cap",
                    "amount": 2274
                }
            },
            "60_to_65": {
                "employee": 0.09,
                "employer": 0.1,
                "total_contribution": {
                    "formula": "employee * salary_cap + employer * salary_cap",
                    "amount": 1396
                }
            },
            "65_to_70": {
                "employee": 0.075,
                "employer": 0.085,
                "total_contribution": {
                    "formula": "employee * salary_cap + employer * salary_cap",
                    "amount": 1155
                },
                "above_70": {
                    "employee": 0.05,
                    "employer": 0.075,
                    "total_contribution": {
                        "formula": "employee * salary_cap + employer * salary_cap",
                        "amount": 925
                    }
                }
            }}
    with open('test_config.json', 'w') as f:
        json.dump(myconfig, f, indent=4)
    #testconfig = ConfigLoader('test_config.json')
    

    # Save the configuration back to the src directory
   # my_config.save('cpf_config_updated.json')