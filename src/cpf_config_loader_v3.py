# config_loader_v2.py
import json
from datetime import datetime, date
import os
from calendar import monthrange
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
                    # Convert to datetime.date instead of datetime.datetime
                    config_data[key] = datetime.strptime(value, DATE_FORMAT).date()
                except ValueError:
                    pass  # not a date-formatted string
            if isinstance(value, dict) and {"year", "month"}.issubset(value.keys()):
                # Convert structured age-based date (if present) to actual date
                year = value.get("year")
                month = value.get("month")
                day = value.get("day")
                if year and month:
                    if day:
                        try:
                            config_data[key + "_DATE"] = date(year, month, day)  # Use date instead of datetime
                        except Exception:
                            pass
                    elif key == "AGE_FOR_BRS_TRANSFER" and "BIRTH_DATE" in config_data:
                        # Compute 55th birthday date from BIRTH_DATE
                        birth_date = config_data["BIRTH_DATE"]
                        transfer_day = birth_date.day
                        try:
                            config_data[key + "_DATE"] = date(year, month, transfer_day)  # Use date instead of datetime
                        except Exception:
                            # Handle edge cases (e.g., Feb 29 birthday)
                            last_day = monthrange(year, month)[1]
                            config_data[key + "_DATE"] = date(year, month, min(transfer_day, last_day))
        self.data = config_data

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Retrieves a value from the nested configuration data.

        Args:
            *keys: One or more string keys representing the path to the desired value.
                   For example, get('loan_payments', 'year_1_2').
            default: The value to return if any key in the path is not found.
                     Defaults to None.

        Returns:
            The requested value, or the default value if not found.
            Returns a copy if the retrieved value is a dictionary to prevent
            unintended modification of the internal configuration.

        Raises:
            ValueError: If no keys are provided.
        """
        if not keys:
            raise ValueError("get() requires at least one key")

        current_value = self.data
        for key in keys:
            if not isinstance(current_value, dict):
                # Cannot traverse further if the current level is not a dictionary
                return default
            current_value = current_value.get(key)
            if current_value is None:
                # Key not found at this level
                return default

        # Return a copy if the final value is a dictionary
        return current_value.copy() if isinstance(current_value, dict) else current_value

    def set(self, key, value):
        # Note: This basic 'set' only works for top-level keys.
        # A nested set would require similar logic to the nested get.
        self.data[key] = value

    def save(self, output_path=None):
        """Save current config data back to JSON (converting datetime to string)."""
        serializable_data = {}
        for key, value in self.data.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = value.strftime(DATE_FORMAT)
            else:
                # Skip internally computed datetime fields on save (they can be regenerated)
                if key.endswith("_DATE") and isinstance(value, (datetime, date)):
                    continue
                serializable_data[key] = value
        out_path = output_path or self.config_path
        with open(out_path, 'w') as f:
            json.dump(serializable_data, f, indent=4)

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
        if not os.path.exists('new__config.json'):
            dummy_data = {
                "START_DATE": "2023-01-15",
                "BIRTH_DATE": "1980-05-20",
                "loan_payments": {
                    "year_1_2": 1687.39,
                    "year_3": 1782.27,
                    "year_4_beyond": 1817.49
                },
                "interest_rates": {
                    "oa_below_55": 2.5,
                    "sa": 4.0
                },
                "some_list": [1, 2, 3]
            }
            with open('new__config.json', 'w') as f:
                json.dump(dummy_data, f, indent=4)
            print("Created dummy new__config.json for testing.")

        config_loader = ConfigLoader('new__config.json')

        # --- Test Cases ---
        # Get top-level value (date object)
        start_date = config_loader.get('START_DATE')
        print(f"START_DATE: {start_date} (Type: {type(start_date)})")

        # Get nested value
        loan_year_3 = config_loader.get('loan_payments', 'year_3')
        print(f"Loan Year 3: {loan_year_3}")

        # Get another nested value
        sa_interest = config_loader.get('interest_rates', 'sa')
        print(f"SA Interest: {sa_interest}")

        # Get a non-dictionary value (list)
        some_list = config_loader.get('some_list')
        print(f"Some List: {some_list}")
        # Try modifying the list (should affect the original if not copied, but get doesn't copy lists)
        # some_list.append(4)
        # print(f"Original data list: {config_loader.data['some_list']}") # Demonstrates list is not copied by default

        # Get a nested dictionary (should be a copy)
        loan_payments_dict = config_loader.get('loan_payments')
        print(f"Loan Payments Dict: {loan_payments_dict}")
        # Modify the copy - should NOT affect the original internal data
        loan_payments_dict['year_3'] = 9999.99
        print(f"Modified Copy: {loan_payments_dict}")
        print(f"Original Internal Data: {config_loader.data['loan_payments']}") # Verify original is unchanged

        # Get non-existent top-level key with default
        missing_top = config_loader.get('NON_EXISTENT_KEY', default='Not Found')
        print(f"Missing Top Key: {missing_top}")

        # Get non-existent nested key with default
        missing_nested = config_loader.get('loan_payments', 'year_5', default=0.0)
        print(f"Missing Nested Key: {missing_nested}")

        # Get key path where intermediate key doesn't exist
        missing_intermediate = config_loader.get('interest_rates', 'invalid_level', 'sa', default='Intermediate Missing')
        print(f"Missing Intermediate Key: {missing_intermediate}")

        # Get key path where intermediate value is not a dict
        invalid_path = config_loader.get('START_DATE', 'some_subkey', default='Invalid Path')
        print(f"Invalid Path (intermediate not dict): {invalid_path}")

        # Test setting a top-level value and saving
        config_loader.set('NEW_KEY', 'New Value Example')
        print(f"Get New Key: {config_loader.get('NEW_KEY')}")
        # config_loader.save('updated_config.json')
        # print("Configuration potentially saved to updated_config.json")

    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")