import json
from src.cpf_data_saver_v2 import DataSaver
from datetime import datetime, date
from typing import Any, Union, List

def custom_serializer(obj):
    """Custom serializer for non-serializable objects like datetime."""
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    # It's better to raise TypeError for unhandled types
    raise TypeError(f"Type {type(obj)} not serializable")

def open_json_file(file_path: str) -> List[dict]:
    """
    Open a JSON file and return its content as a list of dictionaries.
    Each line in the file is expected to be a JSON object.
    """
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]




# the log file format is not really json.
#so parse each line instead of using json.load
def parse_log_file(file_path: str) -> List[dict]:
    """
    Parse a log file and return a list of dictionaries.
    Each line in the log file is expected to be a JSON object.
    """
    logs = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)
                logs.append(log_entry)
            except json.JSONDecodeError:
                continue  # Skip invalid JSON lines
    return logs

def convert_to_dict(logs: List[Union[str, dict]]) -> List[dict]:
    """
    Convert a list of strings or dictionaries to a list of dictionaries.
    """
    result = []
    for item in logs:
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except json.JSONDecodeError:
                continue  # Skip invalid JSON strings
        if isinstance(item, dict):
            result.append(item)
    return result


    
            



