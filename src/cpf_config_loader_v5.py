import json
from datetime import datetime, date
import os
from typing import Any  # Import Any for type hinting

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
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, 'r') as f:
            config_data = json.load(f)
        # Convert date strings to date objects
        for key, value in list(config_data.items()):
            if isinstance(value, str):
                try:
                    config_data[key] = datetime.strptime(value, DATE_FORMAT).date()
                except ValueError:
                    pass  # not a date-formatted string
        self.data = config_data

    def getdata(self, keys, default=None)-> Any:
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

    def add_key_value(self, keys: Any, values: Any):
        """
        Add a new key-value pair to the configuration and save it to the JSON file.
        :param key(s): The key to add or update in the configuration.
        :param value(s): The value to associate with the key.
        """
        
        if isinstance(keys, str) and isinstance(values, str):
            keys = [keys]
            values = [values]
            self.data[keys] = values
            
        elif isinstance(keys, list) and isinstance(values, list):
            if len(keys) != len(values):
                raise ValueError("Keys and values must be of the same length.")
            for key, value in zip(keys, values):
                # Traverse the dictionary to find the correct location
                self.data[key] = value
        elif isinstance(keys, dict) and isinstance(values, dict|None):
            for key, value in keys.items():
                if isinstance(value, dict):
                    # Traverse the dictionary to find the correct location
                    current_dict = self.data
                    for k in key.split('.'):
                        if k not in current_dict:
                            current_dict[k] = {}
                        current_dict = current_dict[k]
                    current_dict.update(value)
                else:
                    self.data[key] = value
        # Save the updated configuration back to the JSON file
        self.save()
       # print(" | ".join(f"Added key '{k}' with value '{v}' to the configuration." for k, v in current_dict.items()))

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
    # Assume 'new__config.json' exists and has content like:
    # {
    #     "START_DATE": "2023-01-01",
    #     "loan_payments": {
    #         "year_1_2": 1687.39,
    #         "year_3": 1782.27,
    #         "year_4_beyond": 1817.49
    #     },
    #     "some_list": [1, 2, 3]
    # }
    try:
        # Create a dummy config for testing if it doesn't exist
        dummy = {
            'some_list_there' : [1, 2, 3]
        }
                                                                                        
        config_loader = ConfigLoader('cpf_config.json')  # Updated file name

        # --- Test Cases ---
        # Get top-level value (date object)
        start_date = config_loader.getdata('START_DATE',0)
        print(f"START_DATE: {start_date} (Type: {type(start_date)})")

        # Get nested value
        loan_year_3 = config_loader.getdata(['loan_payments', 'year_3'],0)
        print(f"Loan Year 3: {loan_year_3}")

        # Get another nested value
        sa_interest = config_loader.getdata(['interest_rates', 'sa'],0)
        print(f"SA Interest: {sa_interest}")
        config_loader.add_key_value('some_list', [1, 2, 3])

        # Get a nested dictionary (should be a copy)
        loan_payments_dict = config_loader.getdata('loan_payments',0)
        print(f"Loan Payments Dict: {loan_payments_dict}")
        # Modify the copy - should NOT affect the original internal data
        loan_payments_dict['year_3'] = 9999.99
        print(f"Modified Copy: {loan_payments_dict}")
        print(f"Original Internal Data: {config_loader.data['loan_payments']}") # Verify original is unchanged

        # Get non-existent top-level key with default
        missing_top = config_loader.getdata('NON_EXISTENT_KEY', 0)
        print(f"Missing Top Key: {missing_top}")

        # Get non-existent nested key with default
        missing_nested = config_loader.getdata(['loan_payments', 'year_5'], 0.0)
        print(f"Missing Nested Key: {missing_nested}")

        # Get key path where intermediate key doesn't exist
        missing_intermediate = config_loader.getdata(['interest_rates', 'invalid_level', 'sa'], 0)
        print(f"Missing Intermediate Key: {missing_intermediate}")

        # Get key path where intermediate value is not a dict
        invalid_path = config_loader.getdata(['START_DATE', 'some_subkey'], 0)
        print(f"Invalid Path (intermediate not dict): {invalid_path}")

        # Test setting a top-level value and saving
        config_loader.add_key_value(['NEW_KEY','2'], ['New Value Example','test'])
        print(f"Get New Key: {config_loader.getdata('NEW_KEY',0)}")
        # config_loader.save('updated_config.json')
        # print("Configuration potentially saved to updated_config.json")
        config_loader.add_key_value(dummy, None)
        config_loader.save('updated_cpf_config.json')
    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")