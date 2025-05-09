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
        self.oa_balance: float = 0.0
        self.sa_balance: float = 0.0
        self.ma_balance: float = 0.0
        self.ra_balance: float = 0.0
        self.loan_balance: float = 0.0
        self.excess_balance: float = 0.0
        self.flow_type: str = ''
        self.message: str = ''
        self.logs = ConfigLoader('cpf_logs.json')
        self.config = ConfigLoader('cpf_config.json')
        self.birth_date = datetime(1974,7,6).date()
        self.age : int = 0   
        self.inflow :float = 0.0
        self.outflow:float  = 0.0                     
    
        
    def convert_dates_to_date(self, xdate: Any, birth_date: Any) -> None:
        """
        Convert xdate and birth_date to date objects and set them as attributes.
        """
        if birth_date is None:
            raise TypeError("birth_date cannot be None")

        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        elif isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        elif not isinstance(birth_date, date):
            raise TypeError(f"birth_date must be a date object, got {type(birth_date)}")

        if xdate is None:
            # Default to today's date if xdate is None
            xdate = datetime.today().date()
        elif isinstance(xdate, str):
            xdate = datetime.strptime(xdate, "%Y-%m-%d").date()
        elif isinstance(xdate, datetime):
            xdate = xdate.date()
        elif not isinstance(xdate, date):
            raise TypeError(f"xdate must be a date object, got {type(xdate)}")

        # Set the attributes directly
        self.birth_date = birth_date
        self.xdate = xdate

    def add_amount(self,amount:float):
        self += amount  
    def subtract_amount(self, amount: float):
        self -= amount
    
    def calculate_age(self) -> int:
        return relativedelta(self.xdate, self.birth_date).years

    def record_inflow(self, account: str, amount: float, message: str = "") -> None:
        """Records an inflow of funds into a specified account."""
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for record_inflow: {account}")
            return
        if not isinstance(amount, (int, float)) or abs(amount) < 1e-9:
            return  # Skip invalid or zero inflow
        # Get current balance safely
        current_balance = getattr(self, f'{account}_balance', 0.0)
        new_balance = current_balance + amount
        # Use the property setter to update balance and trigger logging
        setattr(self, f"{account}_balance", (new_balance.__round__(2)))
        
    def record_outflow(self, account: str, amount: float, message: str = "") -> None:
        """Records an outflow of funds from a specified account."""
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for record_outflow: {account}")
            return
        if not isinstance(amount, (int, float)) or abs(amount) < 1e-9:
            return  # Skip invalid or zero outflow
        # Get current balance safely
        current_balance = getattr(self, f'{account}_balance', 0.0)
        new_balance = current_balance - amount
        # Use the property setter to update balance and trigger logging
        setattr(self, f"{account}_balance", (new_balance.__round__(2) ))
        
    def build_report(self, output_format="csv"):
        """
        Build a report from the logs and save it as a CSV or Excel file.
        :param output_format: The format to save the report ("csv" or "excel").
        """
        # Prepare the report data
        accounts = ["oa", "sa", "ma", "ra", "loan", "excess"]
        report_data = []
        for log in self.logs.data:
            self.xdate = log.get("date",0)
            self.age = self.calculate_age()
            self.account = log.get("account", 0)
            self.old_balance = log.get("old_balance", 0.0)
            self.new_balance = log.get("new_balance", 0.0)
            self.amount = log.get("amount", 0.0)
            self.flow_type = log.get("type", "")
            self.inflow.add_amount(self.amount) if self.flow_type == "inflow" else 0.00
            self.outflow.add_amount(self.amount) if self.flow_type == "outflow" else 0.00
            self.message = log.getdata("message", "")
            self.record_inflow(self.account, self.amount, self.message) if self.amount > 0 else 0.00
            self.record_outflow(self.account, self.amount, self.message) if self.amount > 0 else 0.00

            # Calculate the age for the log's date
           # log_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date()
           

            # Extract year-month for the DATE_KEY
            date_key = self.xdate.strftime("%Y-%m")

            # Append the row to the report data
            report_data.append({
                "DATE_KEY": date_key,
                "AGE": self.age,
                "INFLOW": self.inflow ,
                "OUTFLOW":self.outflow,
                "OA":  self.oa_balance,
                "SA":  self.sa_balance,
                "MA":  self.ma_balance,
                "RA":  self.ma_balance,
                "LOANS":  self.loan_balance,
                "EXCESS": self.excess_balance,
                "TYPE": self.flow_type,
                "MESSAGE": self.message
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
    cpflogs.convert_dates_to_date(cpflogs.xdate, cpflogs.birth_date)
    cpflogs.build_report()
























