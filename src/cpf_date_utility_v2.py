# cpf_program4_v2.py
from datetime import date, datetime # Make sure date is imported
from cpf_config_loader_v2 import ConfigLoader, DATE_FORMAT # Import DATE_FORMAT if needed
from reconfigure_date import MyDateTime
from cpf_date_generator_v2 import generate_date_dict
import json
import os
import sys
from typing import Optional


def run_simulation(config_path: str = None, output_format: str = 'pickle'):
    """Run the CPF simulation using the given config, save results in specified format."""
    # Define the project root directory dynamically
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Add the project root directory to the Python path
    sys.path.append(project_root)

    # Import modules after adding the project root to the path
    from src.cpf_config_loader_v2 import ConfigLoader
    from src.reconfigure_date import MyDateTime
    from src.cpf_date_generator_v2 import generate_date_dict
    from src.cpf_data_saver_v2 import save_results

    # Resolve the default config path if not provided
    if config_path is None:
        config_path = os.path.join(project_root, 'cpf_config.json')

    # Load configuration from JSON

    # Generate the monthly date dictionary for the simulation timeline

    try:
        loader = ConfigLoader(config_path)
        # Use lowercase keys consistent with new_config.json
        start_date_val = loader.get('start_date')
        end_date_val = loader.get('end_date')
        birth_date_val = loader.get('birth_date')

        # Add validation for required date values
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
        start_date = to_date_obj(start_date_val, 'start_date')
        end_date = to_date_obj(end_date_val, 'end_date')
        birth_date = to_date_obj(birth_date_val, 'birth_date')

        if not all([start_date, end_date, birth_date]):
            raise ValueError("One or more dates could not be parsed correctly.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    date_dict = generate_date_dict(start_date=start_date, 
                                   end_date=end_date,
                                   birth_date=birth_date)

    if output_format == 'json':
        # Convert datetime objects to strings for JSON serialization
        serializable_dict = {}
        for key, value in date_dict.items():
            serializable_dict[key] = {
                'period_start': value['period_start'].isoformat(),
                'period_end': value['period_end'].isoformat(),
                'age': value['age']
            }
        save_results(serializable_dict, f"cpf_simulation_results.{output_format}", format=output_format)
    elif output_format == 'pickle':
        save_results(date_dict, f"cpf_simulation_results.{output_format}", format=output_format)
    else:
        print("Invalid output format specified. Choose 'json' or 'pickle'.")
        sys.exit(1)

if __name__ == "__main__":
    run_simulation()