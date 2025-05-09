import json
import re
import pandas as pd
from datetime import datetime, date, strftime
from dateutil.relativedelta import relativedelta

from cpf_config_loader_v5 import ConfigLoader

class Config:
    def __init__(self, config_file: str):
        self.config_loader = ConfigLoader(config_file)
        self.data = []
        self.report = []
        self.birthday = self.config_loader.getdata('birth_date', 0)
        self.today =  datetime.today().strftime("%Y-%m-%d")
        self.age = self.calculate_age(self.birthday, self.today)

    def calculate_age(self, birth_date:date, today:date) -> int:
        """
        Calculate the age in years from birth_date to today.
        :param birth_date: The date of birth.
        :param today: The date to calculate the age at.
        :return: The age in years.
        """
        # Ensure birth_date is a date object
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        elif not isinstance(birth_date, date):
            raise TypeError(f"birth_date must be a date object, got {type(birth_date)}")

        # Ensure today is a date object
        if isinstance(today, str):
            today = datetime.strptime(today, "%Y-%m-%d").date()
        elif not isinstance(today, date):
            raise TypeError(f"today must be a date object, got {type(today)}")
        return relativedelta(today, birth_date).years
    
    def load_data(self):
        # Load data from the JSON file
        try:
            if isinstance(self.data, dict):
                # If data is already a dictionary, no need to load again
                return 
            elif isinstance(self.data, str):
                with open(self.data, 'r') as file:
                    self.data = file.readlines()
            elif isinstance(self.data, list):
                return self.convert_to_dict()
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error loading data: {e}")
        
           
           

    def parse_each_line(self, entry):
        if isinstance(entry, str):
            # use re to determine the start, end of the dictionary
            match = re.search(r'\{.*?\}', entry)
            if match:
                entry = match.group(0)
            else:
                raise ValueError(f"Invalid entry format: {entry}")
        elif isinstance(entry, dict):
            # Convert dict to JSON string
            entry = json.dumps(entry)
        else:
            raise TypeError(f"Unsupported entry type: {type(entry)}")
        # Convert JSON string to dictionary
        try:
            entry = json.loads(entry)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON: {e}")
        return entry
        
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   


    def save_report(self, format='csv'):
        # Save the report to a CSV or Excel file based on the format parameter
        df = pd.DataFrame(self.report)
        if format == 'csv':
            df.to_csv('cpf_report.csv', index=False)
        elif format == 'excel':
            df.to_excel('cpf_report.xlsx', index=False)
            
if __name__ == "__main__":
    # Example usage
    config = Config('cpf_config.json')
    config.load_data()
    config.load_data()
    config.build_report()
    config.save_report(format='csv')  # Save as CSV
    # config.save_report(format='excel')  # Uncomment to save as Excel