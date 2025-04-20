#The error `TypeError: can't compare datetime.datetime to datetime.date` occurs in `cpf_date_generator_v2.py` during the comparison `if start_date > period_end:`. This means that the `start_date` variable and the `period_end` variable have different types - one is a `datetime` object (which includes time information) and the other is a `date` object (which only includes the date).
#
#This inconsistency likely arises from how dates are loaded and processed:
#1.  `ConfigLoader` might parse date strings into `datetime.datetime` objects.
#2.  `run_simulation` in `cpf_date_utility_v2.py` then potentially passes these `datetime` objects (or strings if parsing failed in `ConfigLoader`) to `MyDateTime(...).convert_date()`. The type returned by `convert_date()` is unclear from the provided code but seems to be causing the mismatch.
#3.  Inside `generate_date_dict`, `period_end` is calculated using methods that might preserve the type of `current_date` (which is initialized from `start_date`).
#
#To fix this, we should ensure that all date variables involved in comparisons within `generate_date_dict` are consistently of the same type, preferably `datetime.date` since time information is usually not relevant for these calculations.
#
#**Recommendation:**
#
#Modify `cpf_date_utility_v2.py` to explicitly convert all dates obtained from the configuration into `datetime.date` objects before passing them to `generate_date_dict`. Then, ensure `generate_date_dict` consistently works with `date` objects.
#
#**1. Update `cpf_date_utility_v2.py`:**
#
#```python
# filepath: /workspaces/newcpf_program/src/cpf_date_utility_v2.py
# ... existing imports ...
from datetime import date, datetime # Make sure date is imported
from cpf_config_loader_v2 import ConfigLoader, DATE_FORMAT # Import DATE_FORMAT if needed
from cpf_reconfigure_date_v2 import MyDateTime
from archive.cpf_date_generator_v2 import generate_date_dict
import json

def run_simulation(config_path='new_config.json', output_format='json'):
    """
    Runs the date simulation based on configuration.

    Args:
        config_path (str): Path to the configuration file.
        output_format (str): Desired output format ('json' or 'dict').

    Returns:
        str or dict: Date dictionary in the specified format, or error message.
    """
    try:
        loader = ConfigLoader(config_path)
        # Get date values (might be datetime objects or strings)
        start_date_val = loader.get('start_date')
        end_date_val = loader.get('end_date')
        birth_date_val = loader.get('birth_date')

        # Validate that the values were found
        if not all([start_date_val, end_date_val, birth_date_val]):
             raise ValueError("Missing required date values in the configuration file. Please check 'start_date', 'end_date', and 'birth_date'.")

        # --- Helper function to consistently convert to date objects ---
        def to_date_obj(value, value_name):
            if isinstance(value, datetime):
                return value.date() # Convert datetime to date
            elif isinstance(value, date):
                return value # Already a date object
            elif isinstance(value, str):
                # Try parsing using the standard format first
                try:
                    return datetime.strptime(value, DATE_FORMAT).date()
                except ValueError:
                     # Fallback: Use MyDateTime if standard parsing fails
                     # Assuming MyDateTime.convert_date() returns date or datetime
                     try:
                         converted = MyDateTime(value).convert_date()
                         if isinstance(converted, datetime):
                             return converted.date()
                         elif isinstance(converted, date):
                             return converted
                         else:
                             # Handle case where convert_date returns something unexpected
                             raise ValueError(f"MyDateTime conversion failed for {value_name}")
                     except Exception as e:
                         raise ValueError(f"Error converting '{value_name}' string '{value}' to date: {e}")
            else:
                raise TypeError(f"Unexpected type for {value_name}: {type(value)}")
        # --- End helper function ---

        # Convert all dates to date objects
        start_date_obj = to_date_obj(start_date_val, 'start_date')
        end_date_obj = to_date_obj(end_date_val, 'end_date')
        birth_date_obj = to_date_obj(birth_date_val, 'birth_date')

        # Pass date objects to the generator
        date_dict = generate_date_dict(start_date=start_date_obj, end_date=end_date_obj, birth_date=birth_date_obj)

        # --- Update JSON serialization to handle date objects ---
        if output_format == 'json':
            serializable_dict = {}
            for key, value in date_dict.items():
                serializable_dict[key] = {
                    'period_start': value['period_start'].isoformat(), # isoformat works for date
                    'period_end': value['period_end'].isoformat(),   # isoformat works for date
                    'age': value['age']
                }
            return json.dumps(serializable_dict, indent=4)
        # --- End JSON update ---
        elif output_format == 'dict':
            return date_dict
        else:
            return "Invalid output format specified. Choose 'json' or 'dict'."

    except FileNotFoundError:
        return f"Error: Configuration file not found at {config_path}"
    except (ValueError, TypeError) as ve: # Catch TypeError as well
        return f"Configuration or Date Processing Error: {ve}"
    except Exception as e:
        # Catch other potential errors
        return f"An unexpected error occurred in run_simulation: {e}"

# ... (rest of the file, including if __name__ == "__main__": block) ...
# cpf_program4_v2.pyfrom datetime import date, datetime # Make sure date is importedfrom cpf_config_loader_v2 import ConfigLoader, DATE_FORMAT # Import DATE_FORMAT if neededfrom reconfigure_date import MyDateTimefrom cpf_date_generator_v2 import generate_date_dictimport jsonimport osimport sysfrom typing import Optionaldef run_simulation(config_path: str = None, output_format: str = 'pickle'):    """Run the CPF simulation using the given config, save results in specified format."""    # Define the project root directory dynamically    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # Add the project root directory to the Python path    sys.path.append(project_root)    # Import modules after adding the project root to the path    from src.cpf_config_loader_v2 import ConfigLoader    from src.reconfigure_date import MyDateTime    from src.cpf_date_generator_v2 import generate_date_dict    from src.cpf_data_saver_v2 import save_results    # Resolve the default config path if not provided    if config_path is None:        config_path = os.path.join(project_root, 'cpf_config.json')    # Load configuration from JSON    # Generate the monthly date dictionary for the simulation timeline    try:        loader = ConfigLoader(config_path)        # Use lowercase keys consistent with new_config.json        start_date_val = loader.get('start_date')        end_date_val = loader.get('end_date')        birth_date_val = loader.get('birth_date')        # Add validation for required date values        if not all([start_date_val, end_date_val, birth_date_val]):            raise ValueError("Missing required date values in the configuration file. Please check 'start_date', 'end_date', and 'birth_date'.")        # --- Helper function to consistently convert to date objects ---        def to_date_obj(value, value_name):            if isinstance(value, datetime):                return value.date() # Convert datetime to date            elif isinstance(value, date):                return value # Already a date object            elif isinstance(value, str):                # Try parsing using the standard format first                try:                    return datetime.strptime(value, DATE_FORMAT).date()                except ValueError:                    # Fallback: Use MyDateTime if standard parsing fails                    # Assuming MyDateTime.convert_date() returns date or datetime                    try:                        converted = MyDateTime(value).convert_date()                        if isinstance(converted, datetime):                            return converted.date()                        elif isinstance(converted, date):                            return converted                        else:                            # Handle case where convert_date returns something unexpected                            raise ValueError(f"MyDateTime conversion failed for {value_name}")                    except Exception as e:                        raise ValueError(f"Error converting '{value_name}' string '{value}' to date: {e}")            else:                raise TypeError(f"Unexpected type for {value_name}: {type(value)}")        # --- End helper function ---

        # Convert all dates to date objects
        start_date = to_date_obj(start_date_val, 'start_date')
        end_date = to_date_obj(end_date_val, 'end_date')
        birth_date = to_date_obj(birth_date_val, 'birth_date')

     # Pass date objects to the generator
        date_dict = generate_date_dict(start_date=start_date_obj, end_date=end_date_obj, birth_date=birth_date_obj)

        # --- Update JSON serialization to handle date objects ---
        if output_format == 'json':
            serializable_dict = {}
            for key, value in date_dict.items():
                serializable_dict[key] = {
                    'period_start': value['period_start'].isoformat(), # isoformat works for date
                    'period_end': value['period_end'].isoformat(),   # isoformat works for date
                    'age': value['age']
                }
            return json.dumps(serializable_dict, indent=4)
        # --- End JSON update ---
        elif output_format == 'dict':
            return date_dict
        else:
            return "Invalid output format specified. Choose 'json' or 'dict'."

    except FileNotFoundError:
        return f"Error: Configuration file not found at {config_path}"
    except (ValueError, TypeError) as ve: # Catch TypeError as well
        return f"Configuration or Date Processing Error: {ve}"
    except Exception as e:
        # Catch other potential errors
        return f"An unexpected error occurred in run_simulation: {e}"
        
    

    
    
    
    
 #   
 #   
 #   date_dict = generate_date_dict(start_date=start_date, 
 #                                  end_date=end_date,
 #                                  birth_date=birth_date)
#
 #   if output_format == 'json':
 #       # Convert datetime objects to strings for JSON serialization
 #       serializable_dict = {}
 #       for key, value in date_dict.items():
 #           serializable_dict[key] = {
 #               'period_start': value['period_start'].isoformat(),
 #               'period_end': value['period_end'].isoformat(),
 #               'age': value['age']
 #           }
 #       save_results(serializable_dict, f"cpf_simulation_results.{output_format}", format=output_format)
 #   elif output_format == 'pickle':
 #       save_results(date_dict, f"cpf_simulation_results.{output_format}", format=output_format)
 #   else:
 #       print("Invalid output format specified. Choose 'json' or 'pickle'.")
 #       sys.exit(1)

if __name__ == "__main__":
    run_simulation()