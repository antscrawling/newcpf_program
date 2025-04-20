# cpf_program4_v2.py
import math
from datetime import datetime
import sys
import os

def run_simulation(config_path: str = None, output_format: str = 'pickle'):
    """Run the CPF simulation using the given config, save results in specified format."""
    # Define the project root directory dynamically
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Add the project root directory to the Python path
    sys.path.append(project_root)

    # Import modules after adding the project root to the path
    from src.cpf_config_loader_v2 import ConfigLoader
    from src.cpf_reconfigure_date_v2 import MyDateTime
    from archive.cpf_date_generator_v2 import generate_date_dict
    from src.cpf_data_saver_v2 import save_results

    # Resolve the default config path if not provided
    if config_path is None:
        config_path = os.path.join(project_root, 'cpf_config.json')

    # Load configuration from JSON

    # Generate the monthly date dictionary for the simulation timeline

    try:
        loader = ConfigLoader(config_path)
        start_date = MyDateTime(loader.get('START_DATE')).convert_date()
        end_date = MyDateTime(loader.get('END_DATE')).convert_date()
        birth_date = MyDateTime(loader.get('BIRTH_DATE')).convert_date()
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    date_dict = generate_date_dict(start_date=start_date, 
                                   end_date=end_date,
                                   birth_date=birth_date)

    # Save results
    save_results(date_dict, f"cpf_simulation_results.{output_format}", format=output_format)

if __name__ == "__main__":
    run_simulation()