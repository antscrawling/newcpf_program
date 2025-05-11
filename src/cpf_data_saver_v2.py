# data_saver_v2.py
import json
import pickle
import shelve
from typing import Any, Union, List
import os,csv

SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to the src directory
CONFIG_FILENAME = os.path.join(SRC_DIR, 'cpf_config.json')  # Full path to the config file
LOG_FILE_PATH = os.path.join(SRC_DIR, "cpf_log_file.csv")  # Log file path inside src folder

def save_results(data: Union[dict, List], file_path: str, format: str = None):
    """
    Save the results data to file in the specified format: 'pickle' (binary), 'json', or 'shelve'.
    """
    longfile = os.path.join(SRC_DIR, file_path)
    format = format.lower()
    if format == 'pickle':
        with open(longfile, 'wb') as f:
            pickle.dump(data, f)
    elif format == 'json':
        with open(longfile, 'w') as f:
            json.dump(data, f, default=str, indent=4)
    elif format == 'shelve':
        # Save each item in a shelve DB (useful for incremental storage)
        with shelve.open(longfile, flag='n') as db:
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    db[str(idx)] = item
            elif isinstance(data, dict):
                for key, item in data.items():
                    db[str(key)] = item
            else:
                db['data'] = data
    elif format == 'csv':
        # Save list of dictionaries as a CSV file
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            with open(longfile, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        else:
            raise ValueError("Data must be a list of dictionaries to save as CSV.")
    else:
        raise ValueError(f"Unknown format: {format}")

class DataSaver:
    """
    Class for efficient data storage (optional use). Supports streaming writes in pickle or shelve.
    """
    def __init__(self, format: str = 'pickle'):
        self.format = format.lower()
        self._data_list = []
        if self.format == 'pickle':
            self._file = open('simulation_output.pkl', 'wb')
        elif self.format == 'json':
            self._file = None  # accumulate in memory
        elif self.format == 'shelve':
            self._shelf = shelve.open('simulation_output_shelf.db', flag='n')
        else:
            raise ValueError("Unsupported format for DataSaver")

    def append(self, item: Any):
        """Add an item to storage. If using pickle or shelve, write immediately to avoid memory use."""
        if self.format == 'pickle':
            pickle.dump(item, self._file)
        elif self.format == 'json':
            if isinstance(item, dict):
                self._data_list.append(item)
            else:
                raise ValueError("Item must be a dictionary for JSON format.")
        elif self.format == 'shelve':
            index = len(self._shelf)
            self._shelf[str(index)] = item

    def close(self):
        """Finalize and close the storage, writing any accumulated data for JSON."""
        if self.format == 'pickle':
            self._file.close()
        elif self.format == 'json':
            with open('cpf_logs.json', 'w') as f:
                json.dump(self._data_list, f, default=str, indent=4)
        elif self.format == 'shelve':
            self._shelf.close()
        self._data_list = []
        
if __name__ == "__main__":
    # Example usage
    data = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
    save_results(data, 'test_canbedeleted.json', format='json')
    
    # Using DataSaver
    saver = DataSaver(format='pickle')
    for item in data:
        saver.append(item)
    saver.close()
    
    # Save to CSV
    save_results(data, 'output.csv', format='csv')