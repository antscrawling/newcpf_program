import json
from datetime import datetime, date
import os
from typing import Any  # Import Any for type hinting
import re
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
    
    def flatten_dict(self,d, parent_key="", sep="."):
        """
        Flattens a nested dictionary into a single-level dictionary with keys joined by `sep`.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
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

    def custom_serializer(obj):
        """Custom serializer for non-serializable objects like datetime."""
        if isinstance(obj, (datetime, date)):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        # It's better to raise TypeError for unhandled types
        raise TypeError(f"Type {type(obj)} not serializable")

    def compute_the_values(self):
        """
        Compute the values of the configuration.
        This method can be customized to perform specific calculations or transformations.
        """
        self =  {"cpf_contribution_rates.below_55.total_contribution.amount": 2778,"allocation_above_55.oa.above_70.allocation": 0.08,"allocation_above_55.oa.above_70.formula": "allocation_above_55.oa.above_70.amount = cpf_contribution_rates.below_55.total_contribution.amount * allocation",
                }
        # Example: Convert all string values to uppercase
        for key, value in self.data.items():
            if isinstance(value, dict):
                self.data[key] = value.upper()
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        self.data[key][sub_key] = sub_value.upper()
         


    def evaluate_formulas(self):
        context = {k: v for k, v in self.data.items() if not isinstance(v, str)}

        for key, formula in self.data.items():
            if isinstance(formula, str) and '=' in formula:
                # Extract LHS and RHS from the formula string
                lhs, expr = map(str.strip, formula.split('='))

                # Replace dot-keys in RHS with values from context
                def repl(match):
                    var = match.group(0)
                    return str(context.get(var, 0))  # fallback to 0 if missing

                # Build regex pattern for dot notation keys
                pattern = r"[a-zA-Z_][a-zA-Z0-9_.]*"
                evaluated_expr = re.sub(pattern, repl, expr)

                try:
                    # Safely evaluate the math expression
                    result = eval(evaluated_expr, {"__builtins__": {}}, {})
                    self[lhs] = result
                    context[lhs] = result
                except Exception as e:
                    print(f"Failed to evaluate '{formula}': {e}")

        return self       
    
    def get_nested_value(self,nested, dotted_key):
        """
        Retrieve a value from a nested dictionary using a dotted key.
        :param nested: The nested dictionary to search.
        :param dotted_key: The dotted key string (e.g., "a.b.c").
        :return: The value associated with the dotted key or None if not found.
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
                return None  # Key path broken
        return nested


         
         


# Example usage
if __name__ == "__main__":
    try:
     
        # Load the configuration
        config_loader = ConfigLoader('cpf_config_flat.json')
        config_loader.evaluate_formulas()
    except:
        print('test')
   
   
   
   
       #print(flattened_config)
       #
       #
       #
       #
       #with open('cpf_config_test_flat.json', 'w') as f:
       #    json.dump(flattened_config, f, indent=4, default=config_loader.custom_serializer)
       #
       #
       #
       #
       #
       #
       ## Get keys and values from the configuration
       #  
       #  
       #    
       #exc#pt FileNotFoundError:
       #rint("Configuration file not found.")


