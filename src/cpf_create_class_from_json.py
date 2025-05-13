import os
import json
from datetime import datetime, date


SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to the src directory
CONFIG_FILENAME = os.path.join(SRC_DIR, 'test_config1.json')  # Full path to the config file

class CPFconfig:
    def __init__(self):
        self.class_name: str = None
        self.class_value: str = None

def set_attributes_from_dict(obj, data, parent_key=""):
    """
    Recursively set attributes on an object from a nested dictionary.
    :param obj: The object to set attributes on.
    :param data: The dictionary containing the data.
    :param parent_key: The parent key for nested attributes (used for namespacing).
    """
    for key, value in data.items():
        # Create a namespaced key for nested attributes
        namespaced_key = f"{parent_key}.{key}" if parent_key else key

        if isinstance(value, dict):
            # Recursively process nested dictionaries
            set_attributes_from_dict(obj, value, namespaced_key)
        else:
            # Set the attribute on the object
            setattr(obj, namespaced_key, value)

def main():
    classconfig = CPFconfig()
    # Load the JSON configuration file
    with open(CONFIG_FILENAME, 'r') as config_file:
        config = json.load(config_file)

    # Print the loaded configuration
    print("Loaded configuration:")
    print(json.dumps(config, indent=4))

    # Use the recursive function to set attributes
    set_attributes_from_dict(classconfig, config)

   ## Access attributes
   #print(f"Class name: {getattr(classconfig, 'class_name', None)}")
   #print(f"Class value: {getattr(classconfig, 'class_value', None)}")
   #print(f"Birth date: {getattr(classconfig, 'birth_date', None)}")
   # print(f"OA Allocation: {getattr(classconfig, 'allocation_below_55', None)}")
    #print the entire attributes of the class
    print("All attributes:")
    for attr in dir(classconfig):
        if not attr.startswith('__'):
            print(f"{attr}: {getattr(classconfig, attr)}") 
            
    # get the value 1.0 from self.extra_interest.next_30k_above_55: 1.0
    print(f"{getattr(classconfig, 'extra_interest.next_30k_above_55', None)}")    
    print(f"{getattr(classconfig, 'extra_interest.first_30k_above_55', None)}")
    print(f"{getattr(classconfig, 'start_date', None)}")
if __name__ == "__main__":
    main()















































