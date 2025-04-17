from datetime import datetime
import json
from pprint import pprint
from functools import lru_cache
import logging

logging.basicConfig(level=logging.INFO)


class MyDateTime:
    def __init__(self, date_str):
        self.date_str = date_str

    def check_date(self) -> datetime:
        """
        Converts a date string to a datetime object.
        """
        if isinstance(self.date_str, str):
            try:
                # Parse the date string
                return datetime.strptime(self.date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format: {self.date_str}. Expected format: YYYY-MM-DD.")
        elif isinstance(self.date_str, datetime):
            return self.date_str
        else:
            raise TypeError(f"Expected a string or datetime object, got {type(self.date_str)}")


class MyDateDictGenerator:
    def __init__(self, start_date, birth_date, end_date):
        self.start_date = start_date
        self.birth_date = birth_date
        self.end_date = end_date

    @lru_cache(maxsize=None)
    def get_date_dict(self) -> dict:
        total_months = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month) + 1
        logging.info(f"Generating DATE_DICT for {total_months} months...")

        date_dict = {}
        current_year = self.start_date.year
        current_month = self.start_date.month

        for i in range(total_months):
            date_key = f"{datetime(current_year, current_month, 1).strftime('%b-%Y')}"
            age = current_year - self.birth_date.year - (
                1 if (current_month < self.birth_date.month or 
                      (current_month == self.birth_date.month and self.start_date.day < self.birth_date.day)) else 0
            )
            date_dict[date_key] = {"age": age}

            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

            if i % 100 == 0:  # Log progress every 100 months
                logging.info(f"Processed {i} months...")

        logging.info("DATE_DICT generation complete.")
        return date_dict


def validate_config(config):
    required_keys = ['START_DATE', 'END_DATE', 'BIRTH_DATE']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required key in config.json: {key}")


def get_the_config():
    """
    Reads the config.json file and returns the configuration as a dictionary.
    """
    try:
        # Load the JSON configuration file
        with open('config.json', 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError("The 'config.json' file was not found.")
    except json.JSONDecodeError:
        raise ValueError("The 'config.json' file contains invalid JSON.")

    # Validate required keys in the configuration
    validate_config(config)

    # Convert date fields to datetime objects
    try:
        config['BIRTH_DATE'] = MyDateTime(config['BIRTH_DATE']).check_date()
        config['START_DATE'] = MyDateTime(config['START_DATE']).check_date()
        config['END_DATE'] = MyDateTime(config['END_DATE']).check_date()
    except KeyError as e:
        raise KeyError(f"Missing required key in config.json: {e}")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid date format in config.json: {e}")

    # Generate DATE_DICT
    try:
        date_dict_generator = MyDateDictGenerator(
            start_date=config['START_DATE'],
            birth_date=config['BIRTH_DATE'],
            end_date=config['END_DATE']
        )
        config["DATE_DICT"] = date_dict_generator.get_date_dict()
    except Exception as e:
        raise ValueError(f"Error generating DATE_DICT: {e}")

    return config


if __name__ == "__main__":
    config = get_the_config()
    pprint(config)






















