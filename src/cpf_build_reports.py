from cpf_config_loader_v6 import ConfigLoader
import json
import pandas as pd
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Any


class CPFLogEntry:
    def __init__(self):
        self.xdate: datetime.date = None
        self.age: int = 0
        self.account: str = ''
        self.old_balance: float = 0.0
        self.new_balance: float = 0.0
        self.amount: float = 0.0
        self.flow_type: str = ''
        self.message: str = ''
        self.logs = ConfigLoader('cpf_logs.json')
        self.config = ConfigLoader('cpf_config.json')
        self.birth_date = datetime.date(1974,7,6)
        
        self.age = 0                        
        
    def convert_dates_to_date(self, xdate: Any, birth_date: Any):
        
        """
        Calculate the age based on the birth_date and today's date.
        """
        if isinstance(self.birth_date, str):
            self.birth_date = datetime.strptime(self.birth_date, "%Y-%m-%d").date()
        elif isinstance(self.birth_date, datetime):
            self.birth_date = self.birth_date.date()
        elif isinstance(self.birth_date, date):
            self.birth_date = self.birth_date
        elif isinstance(self.date, str):
            self.date = datetime.strptime(self.date, "%Y-%m-%d").date()
        elif isinstance(self.date, datetime):
            self.date = self.date.date()
        elif isinstance(self.date, date):
            self.date = self.date
        else:
            raise TypeError(f"birth_date must be a date object, got {type(self.birth_date)}")

        #setattr(self,xdate, self.date)
        setattr(self,birth_date, self.birth_date)
        setattr(self, xdate, self.date)

    def add_amount(self,amount:float):
        self += amount
    def subtract_amount(self, amount: float):
        self -= amount
    
    def build_report(self, output_format="csv"):
        """
        Build a report from the logs and save it as a CSV or Excel file.
        :param output_format: The format to save the report ("csv" or "excel").
        """
        # Prepare the report data
        report_data = []
        for log in self.logs.data:
            self.date = log.getdata("date", "")
            self.age = self.age
            self.account = log.get("account", "")
            self.old_balance = log.get("old_balance", 0.0)
            self.new_balance = log.get("new_balance", 0.0)
            self.amount = log.get("amount", 0.0)
            self.flow_type = log.get("type", "")
            self.message = log.get("message", "")

            # Calculate the age for the log's date
            log_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date()
            age = relativedelta(log_date, self.birth_date).years

            # Extract year-month for the DATE_KEY
            date_key = log_date.strftime("%Y-%m")

            # Append the row to the report data
            report_data.append({
                "DATE_KEY": date_key,
                "AGE": age,
                "INFLOW": amount if flow_type == "inflow" else 0.0,
                "OUTFLOW": amount if flow_type == "outflow" else 0.0,
                "OA": new_balance if account == "oa" else 0.0,
                "SA": new_balance if account == "sa" else 0.0,
                "MA": new_balance if account == "ma" else 0.0,
                "RA": new_balance if account == "ra" else 0.0,
                "LA": new_balance if account == "la" else 0.0,
                "EA": new_balance if account == "ea" else 0.0,
                "TYPE": flow_type,
                "MESSAGE": message
            })

        # Convert the report data to a DataFrame
        df = pd.DataFrame(report_data)

        # Save the report as CSV or Excel
        output_file = f"cpf_report.{output_format}"
        if output_format == "csv":
            df.to_csv(output_file, index=False)
        elif output_format == "excel":
            df.to_excel(output_file, index=False, engine="openpyxl")
        else:
            raise ValueError("Invalid output format. Use 'csv' or 'excel'.")

        print(f"Report saved as {output_file}")


if __name__ == "__main__":
    # Example usage
    cpflogs = CPFLogEntry()
 #   cpflogs.build_report(output_format="csv")  # Change to "excel" for Excel output

























