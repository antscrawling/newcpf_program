# data_saver_v2.py
import json
import pickle
import shelve
import pandas as pd
import csv
from datetime import datetime
from typing import Any, Union, List

def save_results(data: Union[dict, List], file_path: str, format: str = None):
    """
    Save the results data to file in the specified format: 'pickle' (binary), 'json', 'shelve', or 'csv'.
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
    elif format == 'csv':
        # Save list of dictionaries as a CSV file
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        else:
            raise ValueError("Data must be a list of dictionaries to save as CSV.")
    else:
        raise ValueError(f"Unknown format: {format}")

class DataSaver:
    """
    Class for efficient data storage (optional use). Supports streaming writes in pickle, shelve, or csv.
    """
    def __init__(self, format: str = None,filename: str = None):
        self.format = format.lower()
        self._data_list = []
        if self.format == 'pickle':
            self._file = open(filename, 'wb')
        elif self.format == 'json':
            self._file = None  # accumulate in memory
        elif self.format == 'shelve':
            self._shelf = shelve.open('filename', flag='n')
        elif self.format == 'csv':
            self._file = open(filename, 'w', newline='')
            self._csv_writer = None  # Initialize later when the first item is appended
        else:
            raise ValueError("Unsupported format for DataSaver")

    def append(self, item: Any):
        """Add an item to storage. If using pickle, shelve, or csv, write immediately to avoid memory use."""
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
        elif self.format == 'csv':
            if isinstance(item, dict):
                if self._csv_writer is None:
                    # Initialize the CSV writer with the fieldnames from the first item
                    self._csv_writer = csv.DictWriter(self._file, fieldnames=item.keys())
                    self._csv_writer.writeheader()
                self._csv_writer.writerow(item)
            else:
                raise ValueError("Item must be a dictionary for CSV format.")

    def close(self):
        """Finalize and close the storage, writing any accumulated data for JSON."""
        if self.format == 'pickle':
            self._file.close()
        elif self.format == 'json':
            with open('cpf_logs.json', 'w') as f:
                json.dump(self._data_list, f, default=str, indent=4)
        elif self.format == 'shelve':
            self._shelf.close()
        elif self.format == 'csv':
            self._file.close()
        self._data_list = []

    def build_report(self, output_format="csv"):
        """
        Build a report from the logs and save it as a CSV or Excel file.
        :param output_format: The format to save the report ("csv" or "excel").
        """
        report_data = []

        # Ensure logs are loaded
        if self.logs is None or self.logs.empty:
            raise ValueError("Logs data is empty or not loaded.")

        for _, log in self.logs.iterrows():
            # Extract log details
            date_str = log["date"]
            try:
                # Try parsing as full datetime
                self.xdate = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                try:
                    # Try parsing as year-month
                    self.xdate = datetime.strptime(date_str, "%Y-%m").date()
                except ValueError:
                    raise ValueError(f"Invalid date format: {date_str}")

            # Update the age for the current log entry
            self.age = self.calculate_age()

            self.flow_type = log["type"]
            self.message = log["message"]

            account = log["account"]
            amount = log["amount"]

            if self.flow_type == "inflow":
                self.record_inflow(account, amount, self.message)
            elif self.flow_type == "outflow":
                self.record_outflow(account, amount, self.message)

            # Extract year-month for the DATE_KEY
            date_key = self.xdate.strftime("%Y-%m")

            # Append the row to the report data
            report_data.append({
                "DATE_KEY": date_key,
                "AGE": self.age,
                "INFLOW": self.inflow,
                "OUTFLOW": self.outflow,
                "OA": self.oa_balance,
                "SA": self.sa_balance,
                "MA": self.ma_balance,
                "RA": self.ra_balance,
                "LOANS": self.loan_balance,
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