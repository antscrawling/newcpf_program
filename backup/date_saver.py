# data_saver_v2.py
import json, pickle, shelve
from typing import Any, Union, List

def save_results(data: Union[dict, List], file_path: str, format: str = 'pickle'):
    """
    Save the results data to file in the specified format: 'pickle' (binary), 'json', or 'shelve'.
    """
    format = format.lower()
    if format == 'pickle':
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
    elif format == 'json':
        with open(file_path, 'w') as f:
            json.dump(data, f, default=str, indent=4)
    elif format == 'shelve':
        # Save each item in a shelve DB (useful for incremental storage)
        with shelve.open(file_path, flag='n') as db:
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    db[str(idx)] = item
            elif isinstance(data, dict):
                for key, item in data.items():
                    db[str(key)] = item
            else:
                db['data'] = data
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
            self._data_list.append(item)
        elif self.format == 'shelve':
            index = len(self._shelf)
            self._shelf[str(index)] = item

    def close(self):
        """Finalize and close the storage, writing any accumulated data for JSON."""
        if self.format == 'pickle':
            self._file.close()
        elif self.format == 'json':
            with open('simulation_output.json', 'w') as f:
                json.dump(self._data_list, f, default=str, indent=4)
        elif self.format == 'shelve':
            self._shelf.close()
        self._data_list = [] 