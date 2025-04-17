# config_loader_v2.py
import json
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"

class ConfigLoader:
    """
    Load config from JSON, converting date strings to datetime objects.
    Also supports saving the config back to JSON (round-trip).
    """
    def __init__(self, config_path):
        self.config_path = config_path
        self.data = None
        self._load_config()

    def _load_config(self):
        with open(self.config_path, 'r') as f:
            config_data = json.load(f)
        # Convert date strings to datetime objects
        for key, value in list(config_data.items()):
            if isinstance(value, str):
                try:
                    config_data[key] = datetime.strptime(value, DATE_FORMAT)
                except ValueError:
                    pass  # not a date-formatted string
            if isinstance(value, dict) and {"year", "month"}.issubset(value.keys()):
                # Convert structured age-based date (if present) to actual datetime
                year = value.get("year")
                month = value.get("month")
                day = value.get("day")
                if year and month:
                    if day:
                        try:
                            config_data[key + "_DATE"] = datetime(year, month, day)
                        except Exception:
                            pass
                    elif key == "AGE_FOR_BRS_TRANSFER" and "BIRTH_DATE" in config_data:
                        # Compute 55th birthday date from BIRTH_DATE
                        birth_date = config_data["BIRTH_DATE"]
                        transfer_day = birth_date.day
                        try:
                            config_data[key + "_DATE"] = datetime(year, month, transfer_day)
                        except Exception:
                            # Handle edge cases (e.g., Feb 29 birthday)
                            from calendar import monthrange
                            last_day = monthrange(year, month)[1]
                            config_data[key + "_DATE"] = datetime(year, month, min(transfer_day, last_day))
        self.data = config_data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def save(self, output_path=None):
        """Save current config data back to JSON (converting datetime to string)."""
        serializable_data = {}
        for key, value in self.data.items():
            if isinstance(value, datetime):
                serializable_data[key] = value.strftime(DATE_FORMAT)
            else:
                # Skip internally computed datetime fields on save (they can be regenerated)
                if key.endswith("_DATE") and isinstance(value, datetime):
                    continue
                serializable_data[key] = value
        out_path = output_path or self.config_path
        with open(out_path, 'w') as f:
            json.dump(serializable_data, f, indent=4)