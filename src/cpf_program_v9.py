import atexit
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from pprint import pprint
#from dateutility import  MyDateDictGenerator
import json
from cpf_config_loader_v4 import ConfigLoader
from cpf_reconfigure_date_v2 import MyDateTime

from collections import OrderedDict
import inspect
from multiprocessing import Process, Queue
from queue import Empty

# Load configuration
config = ConfigLoader('cpf_config.json')

# Define the worker function at the top level (outside the class)
def _save_log_worker(queue, filename):
    """Worker process to save logs to a file."""
    with open(filename, 'a') as file:
        while True:
            try:
                log_entry = queue.get(timeout=1)  # Wait for a log entry with a timeout
                if log_entry == "STOP":
                    break
                # Use the top-level serializer function
                file.write(json.dumps(log_entry, default=custom_serializer) + '\n')
            except Exception:  # Consider more specific exception handling (e.g., queue.Empty)
                # Handle timeout or other exceptions gracefully
                # Check if the queue is empty after timeout before continuing
                if queue.empty():
                    continue

# Define the custom serializer at the top level or as a static method
def custom_serializer(obj):
    """Custom serializer for non-serializable objects like datetime."""
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    # It's better to raise TypeError for unhandled types
    raise TypeError(f"Type {type(obj)} not serializable")



class CPFAccount:
    def __init__(self, config_loader):  # Accept config_loader
        self.config = config_loader  # Store the config_loader instance
        self.current_date = datetime.now()
        self.date_key : str = None
        self.message : str = None
        self.start_date = None
        self.end_date = None
        self.birth_date = None
        self.salary = self.config.getdata('salary', 0.0)
        self.age = 0
        self._oa_allocation55      = 0.0
        self._sa_allocation55      = 0.00
        self._ma_allocation55      = 0.00
        self._ra_allocation55      = 0.00
        self._oa_allocation5560   = 0.00
        self._sa_allocation5560   = 0.00
        self._ma_allocation5560   = 0.00
        self._ra_allocation5560   = 0.00
        self._oa_allocation6065    = 0.00
        self._ma_allocation6065    = 0.00
        self._ra_allocation6065    = 0.00
        self._oa_allocation6570    = 0.00
        self._ma_allocation6570    = 0.00
        self._ra_allocation6570    = 0.00
        self._oa_allocation70      = 0.00
        self._ma_allocation70      = 0.00
        self._ra_allocation70      = 0.00
  
        # Account balances and logs
        self._oa_balance = 0.0
        self._oa_log = []
        self._oa_message = ""
        self._oa_allocation = 0.0

        self._sa_balance = 0.0
        self._sa_log = []
        self._sa_message = ""
        self._sa_allocation = 0.0

        self._ma_balance = 0.0
        self._ma_log = []
        self._ma_message = ""
        self._ma_allocation = 0.0

        self._ra_balance = 0.0
        self._ra_log = []
        self._ra_message = ""
        self._ra_allocation = 0.0
        
        self.employer_contribution = 0.0
        self.employee_contribution = 0.0
        self.total_contribution = 0.0

        self._excess_balance = 0.0
        self._excess_balance_log = []
        self._excess_message = ""

        self._loan_balance = 0.0
        self._loan_balance_log = []
        self._loan_message = ""       
        
        self._combined_balance = 0.0
        self._combined_balance_log = []
        self._combined_message = ""
        
        self._combinedbelow55_balance = 0.0
        self._combinedbelow55_log = []
        self._combinedbelow55_message = ""
        
        self._combinedabove55_balance = 0.0
        self._combinedabove55_log = []
        self._combinedabove55_message = ""
       
        
        # Log saving setup
        self.log_queue = Queue()
        # Use the top-level worker function as the target
        # Pass only the queue and filename, which are picklable
        datestring = self.current_date.strftime("%Y%m%d")
        self.log_process = Process(target=_save_log_worker, args=(self.log_queue, f'cpf_logs{datestring}.json'))
        self.log_process.daemon = True  # Ensure the process terminates with the main program
        self.log_process.start()

        # Register cleanup function
        atexit.register(self.close_log_writer)

    def save_log_to_file(self, log_entry):
        """Send log entry to the worker process."""
        # Check if the process is alive before putting item in queue
        if self.log_process.is_alive():
            self.log_queue.put(log_entry)
        else:
            # Handle the case where the log process might have died unexpectedly
            print("Warning: Log writer process is not running.")
            # Optionally, try restarting it or log to stderr

    def close_log_writer(self):
        """Stop the log writer process."""
        # Check if the process exists and is alive before trying to stop it
        if hasattr(self, 'log_process') and self.log_process.is_alive():
            try:
                self.log_queue.put("STOP")  # Send the stop signal
                self.log_process.join(timeout=5)  # Wait for the process to terminate
                if self.log_process.is_alive():
                    # If it's still alive after timeout, terminate it forcefully
                    self.log_process.terminate()
                    self.log_process.join()  # Wait for termination
            except Exception as e:
                print(f"Error closing log writer: {e}")  # Log potential errors during shutdown
        # Clean up queue reference
        if hasattr(self, 'log_queue'):
            self.log_queue.close()
            self.log_queue.join_thread()

    @property
    def oa_balance(self):
        return self._oa_balance, self._oa_message

    @oa_balance.setter
    def oa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._oa_balance
        log_entry = {
            'date': self.date_key,
            'account': 'oa',
            'old_balance': self._oa_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'oa-{self.message}-{diff:.2f}'
        }
        self._oa_balance = value.__round__(2)
        self._oa_message = self.message
        self.save_log_to_file(log_entry)

    @property
    def sa_balance(self):
        return self._sa_balance, self._sa_message

    @sa_balance.setter
    def sa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            # Ensure value is treated as float if data is not a tuple/list
            value, message = float(data), "no message"  # Assuming data should be numeric
        diff = value - self._sa_balance
        log_entry = {
            # Ensure current_date is set before logging
            'date': self.date_key,
            'account': 'sa',  # Add account identifier
            'old_balance': self._sa_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'sa-{self.message}-{diff:.2f}'  # Format diff for consistency
        }
        # self._sa_log.append(log_entry) # Optional: Keep in-memory log if needed
        self._sa_balance = value.__round__(2)
        self._sa_message = self.message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    @property
    def ma_balance(self):
        return self._ma_balance, self._ma_message

    @ma_balance.setter
    def ma_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._ma_balance
        log_entry = {
            'date': self.date_key,
            'account': 'ma',
            'old_balance': self._ma_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'ma-{self.message}-{diff:.2f}'
        }
        self._ma_balance = value.__round__(2)
        self._ma_message = self.message
        self.save_log_to_file(log_entry)

    @property
    def ra_balance(self):
        return self._ra_balance, self._ra_message

    @ra_balance.setter
    def ra_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._ra_balance
        log_entry = {
            'date': self.date_key,
            'account': 'ra',
            'old_balance': self._ra_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'ra-{self.message}-{diff:.2f}'
        }
        self._ra_balance = value
        self._ra_message = self.message
        self.save_log_to_file(log_entry)

    @property
    def excess_balance(self):
        return self._excess_balance, self._excess_message

    @excess_balance.setter
    def excess_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._excess_balance
        log_entry = {
            'date': self.date_key,
            'account': 'excess',
            'old_balance': self._excess_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'excess-{self.message}-{diff:.2f}'
        }
        self._excess_balance = value.__round__(2)
        self._excess_message = self.message
        self.save_log_to_file(log_entry)

    @property
    def loan_balance(self):
        return self._loan_balance, self._loan_message

    @loan_balance.setter
    def loan_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._loan_balance
        log_entry = {
            'date': self.date_key,
            'account': 'loan',
            'old_balance': self._loan_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'loan-{self.message}-{diff:.2f}'
        }
        self._loan_balance = value.__round__(2)
        self._loan_message = self.message
        self.save_log_to_file(log_entry)

    @property
    def combined_balance(self):
        # Always calculate the combined balance dynamically
        self._combined_balance = (
            self._oa_balance +
            self._sa_balance +
            self._ma_balance +
            self._ra_balance
        )
        return self._combined_balance, self._combined_message

    @combined_balance.setter
    def combined_balance(self, data):
        # Setter logic remains unchanged
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._combined_balance
        log_entry = {
            'date': self.date_key,
            'account': 'combined',
            'old_balance': self._combined_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'combined-{self.message}-{diff:.2f}'
        }
        self._combined_balance = value.__round__(2)
        self._combined_message = self.message
        self.save_log_to_file(log_entry)

    @property
    def combinedbelow55_balance(self):
        # Dynamically calculate the combined below 55 balance if age <= 55
        if self.current_date and self.birth_date:
            age = (self.current_date.year - self.birth_date.year) - (
                (self.current_date.month, self.current_date.day) < (self.birth_date.month, self.birth_date.day)
            )
            if age < 55:
                self._combinedbelow55_balance = (
                    self._oa_balance +
                    self._sa_balance +
                    self._ma_balance
                )
        return self._combinedbelow55_balance, self._combinedbelow55_balance_message

    @combinedbelow55_balance.setter
    def combinedbelow55_balance(self, data):
        # Setter logic remains unchanged
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._combinedbelow55_balance
        log_entry = {
            'date': self.date_key,
            'account': 'combined_below_55',
            'old_balance': self._combinedbelow55_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'combined_below_55-{self.message}-{diff:.2f}'
        }
        self._combinedbelow55_balance = value.__round__(2)
        self._combinedbelow55_balance_message = self.message
        self.save_log_to_file(log_entry)

    @property
    def combinedabove55_balance(self):
        # Dynamically calculate the combined above 55 balance if age >= 55
        if self.current_date and self.birth_date:
            age = (self.current_date.year - self.birth_date.year) - (
                (self.current_date.month, self.current_date.day) < (self.birth_date.month, self.birth_date.day)
            )
            if age >= 55:
                self._combinedabove55_balance = (
                    self._oa_balance +
                    self._ra_balance +
                    self._ma_balance
                )
        return self._combinedabove55_balance, self._combinedabove55_balance_message

    @combinedabove55_balance.setter
    def combinedabove55_balance(self, data):
        # Setter logic remains unchanged
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, self.message = data
        else:
            value, self.message = float(data), "no message"
        diff = value - self._combinedabove55_balance
        log_entry = {
            'date': self.date_key,
            'account': 'combined_above_55',
            'old_balance': self._combinedabove55_balance.__round__(2),
            'new_balance': value.__round__(2),
            'amount': diff.__round__(2),
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'combined_above_55-{self.message}-{diff:.2f}'
        }
        self._combinedabove55_balance = value.__round__(2)
        self._combinedabove55_balance_message = self.message
        self.save_log_to_file(log_entry)

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and ensure resources are released."""
        self.close_log_writer()
        return False

    def close(self):
        """Ensure the log writer process is properly closed."""
        self.close_log_writer()

    def get_date_dict(self, start_date, end_date, birth_date):
        """Generate a date dictionary.  #this is called once only """
        print("Warning: get_date_dict needs implementation in CPFAccount or be imported correctly.")
        from cpf_date_generator_v3 import generate_date_dict
        return generate_date_dict(start_date, end_date, birth_date)
    def update_balance(self, account: str, new_balance: float, message: str):
        """
        Sets the account balance to the specified new_balance and logs the change.
        The logged 'amount' reflects the difference from the old balance.
        # this is called every month
        """
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for update_balance: {account}")
            return # Or raise ValueError
        # Set the new balance using the provided value
        setattr(self, f"_{account}_balance", new_balance)

    def record_inflow(self, account: str, amount: float, message: str = None):
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for record_inflow: {account}")
            return

        if not isinstance(amount, (int, float)) or abs(amount) < 1e-9:
            return  # Skip invalid or zero inflow

        # Get current balance safely
        current_balance = getattr(self, f'_{account}_balance', 0.0)
        new_balance = current_balance + amount

        # Use the property setter to update balance and trigger logging
        setattr(self, f"{account}_balance", (new_balance.__round__(2), message))

    def record_outflow(self, account: str, amount: float, message: str = None):
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for record_outflow: {account}")
            return

        if not isinstance(amount, (int, float)) or abs(amount) < 1e-9:
            return  # Skip invalid or zero outflow

        # Get current balance safely
        current_balance = getattr(self, f'_{account}_balance', 0.0)
        new_balance = current_balance - amount

        # Use the property setter to update balance and trigger logging
        setattr(self, f"{account}_balance", (new_balance.__round__(2), message ))


    def calculate_cpf_allocation(self, account: str) -> float:
        """
        Calculates the allocation amount for a specific CPF account based on age and total CPF contribution.
        """
        # Ensure total contributions are calculated
        if self.total_contribution == 0.0:
            raise ValueError("Total contributions have not been calculated. Call `calculate_total_contributions` first.")

        # Determine allocation rates based on age
        if self.age < 55:
            alloc_percentage = self.config.getdata(['allocation_below_55',account],0)
            self._oa_allocation55 = alloc_percentage * self.total_contribution
            self._sa_allocation55 = alloc_percentage * self.total_contribution
            self._ma_allocation55 = alloc_percentage * self.total_contribution
            self._ra_allocation55 = 0.0
           
        elif 55 <= self.age < 60:
            alloc_percentage = self.config.getdata(['allocation_above_55',account,'56_to_60'], 0)
            self._oa_allocation_5560 = alloc_percentage * self.total_contribution
            self._sa_allocation_5560 = alloc_percentage * self.total_contribution if self.age <= 55 else 0.0
            self._ma_allocation_5560 = alloc_percentage * self.total_contribution
            self._ra_allocation_5560 = alloc_percentage * self.total_contribution if self.age > 55 else 0.0
        elif 60 <= self.age < 65:
            alloc_percentage = self.config.getdata(['allocation_above_55',account,'61_to_65'], 0)
            self._oa_allocation6065 = alloc_percentage * self.total_contribution
            self._ma_allocation6065 = alloc_percentage * self.total_contribution
            self._ra_allocation6065 = alloc_percentage * self.total_contribution 
           
        elif 65 <= self.age < 70:
            alloc_percentage = self.config.getdata(['allocation_above_55', account,'66_to_70'],0)
            self._oa_allocation6570 = alloc_percentage * self.total_contribution
            self._ma_allocation6570 = alloc_percentage * self.total_contribution
            self._ra_allocation6570 = alloc_percentage * self.total_contribution 
     
        else:  # age >= 70
            alloc_percentage = self.config.getdata(['allocation_above_55',account,'above_70'], 0)
            self._oa_allocation70 = alloc_percentage * self.total_contribution
            self._ma_allocation70 = alloc_percentage * self.total_contribution
            self._ra_allocation70 = alloc_percentage * self.total_contribution          

        # Calculate the allocation amount
        allocation_amount = self.total_contribution * alloc_percentage
        return allocation_amount

    def compute_and_add_allocation(self):
        """
        Compute the CPF allocation amounts for each category (oa, sa, ma, ra) based on the age
        and add them to the configuration using the add_key_value method.
        """
        # Retrieve the salary cap
        salary_cap = self.config.getdata('salary_cap', 0)
        self.calculate_total_contributions()
        allocation = {}
        mydict = {}
        with open('cpf_config.json', 'r') as file:
            mydict = json.load(file) 
        # Determine the correct age bracket for contribution rates
        allocation =   {"allocation_below_55": {
                        "oa": {"allocation":0.6217,"amount": 0.6217 * self.total_contribution},
                        "sa": {"allocation":0.1621,"amount": 0.1621 * self.total_contribution},
                        "ma": {"allocation":0.2162,"amount": 0.2162 * self.total_contribution}},
                        "allocation_above_55": {
       "oa": {
           "56_to_60": {"allocation":0.3694,   "amount": 0.3694 * self.total_contribution },
           "61_to_65": {"allocation":0.149,    "amount": 0.149  * self.total_contribution },
           "66_to_70": {"allocation":0.0607,   "amount": 0.0607 * self.total_contribution },
           "above_70": {"allocation":0.08,     "amount": 0.08  * self.total_contribution }
       },
       "sa": {"allocation":0.00, "amount": 0.0 },
       "ma": {
           "56_to_60": {"allocation":0.323       ,"amount" : 0.323  * self.total_contribution },
           "61_to_65": {"allocation":0.4468      ,"amount" : 0.4468 * self.total_contribution },
           "66_to_70": {"allocation":0.6363      ,"amount" : 0.6363 * self.total_contribution },
           "above_70": {"allocation":0.84        ,"amount" : 0.84   * self.total_contribution },
       },
       "ra": {
           "56_to_60": {"allocation":0.3076,    "amount" : self.total_contribution * 0.3076 },
           "61_to_65": {"allocation":0.4042,    "amount" : self.total_contribution * 0.4042 },
           "66_to_70": {"allocation":0.303,     "amount" : self.total_contribution * 0.303 },
           "above_70": {"allocation":0.08 ,     "amount" : self.total_contribution * 0.08  }
       }
                                                },  
            }
        allocation.update(mydict)
        with open ('cpf_config.json', 'w') as file:
            json.dump(allocation, file, indent=4)
       # self.config.add_key_value(allocation, None)
       # self.config.save()

    def calculate_combined_balance(self):
        ''' calculate the combined balance based on age '''
        oa_balance = 0.0
        sa_balance = 0.0
        ma_balance = 0.0
        ra_balance = 0.0
        
        
        if self.age < 55:
            #                       10_000                     -->  10_000
            oa_balance = min(getattr(self, '_oa_balance', 0), 20_000)
            #                       50_000                    -->   40_000       
            sa_balance = min(getattr(self, '_sa_balance', 0), 40_000 )
            if (oa_balance + sa_balance) == 60_000:
                return oa_balance, sa_balance, 0.00, 0.00
            ma_balance = min(getattr(self, '_ma_balance', 0), 40_000 )
            if (oa_balance + sa_balance + ma_balance) == 60_000:
                return oa_balance, sa_balance, ma_balance, 0.00
            ra_balance = 0.00
            return oa_balance, sa_balance, ma_balance, ra_balance
        elif self.age >= 55:
            #                       50000                     -->  20000
            oa_balance = min(getattr(self, '_oa_balance', 0), 20_000)
           # sa_balance = min(getattr(self, '_sa_balance', 0), 10_000)
           #if (oa_balance + sa_balance) == 30_000:
           #    return oa_balance, sa_balance, 0.00, 0.00
            ma_balance = min(getattr(self, '_ma_balance',0),  30_000 - oa_balance)
            if (oa_balance  + ma_balance) == 30_000:
                return oa_balance, sa_balance, ma_balance, ra_balance
            ra_balance = min(getattr(self, '_ra_balance', 0), 30_000)
            if (oa_balance + ma_balance + ra_balance) == 60_000:
                return oa_balance, sa_balance, ma_balance, ra_balance
            return oa_balance, sa_balance, ma_balance, ra_balance                                                                                                                     
        
    def calculate_interest_on_cpf(self, account: str, amount: float) -> float:
        """
        Apply interest to all CPF accounts at the end of the year.
        This is called every December - 12 of every year.
        """
        # Retrieve interest rates from the configuration
        oa_rate = self.config.getdata(['interest_rates', 'oa_below_55'], 2.5) if self.age < 55 else self.config.getdata(['interest_rates', 'oa_above_55'], 4.0)
        sa_rate = self.config.getdata(['interest_rates', 'sa'], 4.0)
        ma_rate = self.config.getdata(['interest_rates', 'ma'], 4.0)
        ra_rate = self.config.getdata(['interest_rates', 'ra'], 4.0)

        # Calculate interest based on the account type
        if account == 'oa':
            return round((oa_rate / 100 / 12) * amount, 2)
        elif account == 'sa':
            return round((sa_rate / 100 / 12) * amount, 2)
        elif account == 'ma':
            return round((ma_rate / 100 / 12) * amount, 2)
        elif account == 'ra':
            return round((ra_rate / 100 / 12) * amount, 2)
        else:
            raise ValueError("Invalid account type. Must be 'oa', 'sa', 'ma', or 'ra'.")
            
                                                                                                           
    def calculate_extra_interest(self):
        """
        Apply extra interest to SA and MA accounts based on age.
        This is called every December - 12 of every year.
        """
        extra_interest = self.config.getdata(['extra_interest'], {})
        extra_interest_rate = self.config.getdata(['extra_interest', 'below_55'], 1.0)
        extra_interest1 = self.config.getdata(['extra_interest', 'first_30k_above_55'], 2.0)
        extra_interest2 = self.config.getdata(['extra_interest', 'next_30k_above_55'], 1.0)
        oa_interest = 0.0
        sa_interest = 0.0
        ma_interest = 0.0
        ra_interest = 0.0
        oa_balance, sa_balance, ma_balance, ra_balance = self.calculate_combined_balance()

        if self.age < 55:
            oa_interest = oa_balance * (extra_interest_rate / 100 / 12)
            sa_interest = sa_balance * (extra_interest_rate / 100 / 12)
            ma_interest = ma_balance * (extra_interest_rate / 100 / 12)
            ra_interest = 0.0
            return (0, oa_interest + sa_interest, ma_interest, ra_interest)
        elif self.age >= 55:
            first_30k = min((oa_balance + sa_balance + ma_balance + ra_balance), 30_000)
            next_30k = min(oa_balance + sa_balance + ma_balance + ra_balance - first_30k, 30_000)

            if first_30k == 30_000:
                ra_interest = 30_000 * (extra_interest1 / 100 / 12)
            elif next_30k == 30_000:
                ra_interest = 30_000 * (extra_interest2 / 100 / 12)
            else:
                ra_interest = 0.0

            return (oa_interest, sa_interest, ma_interest, ra_interest)
    
    def get_cpf_contribution_rate(self, age: int, is_employee: bool) -> float:
        """
        Retrieve CPF contribution rate based on age and employment status.
        """
        if age < 55:
            rates = self.config.getdata(['cpf_contribution_rates', 'below_55'], {})
        elif 55 <= age < 60:
            rates = self.config.getdata(['cpf_contribution_rates', '55_to_60'], {})
        elif 60 <= age < 65:
            rates = self.config.getdata(['cpf_contribution_rates', '60_to_65'], {})
        elif 65 <= age < 70:
            rates = self.config.getdata(['cpf_contribution_rates', '65_to_70'], {})
        else:
            rates = self.config.getdata(['cpf_contribution_rates', 'above_70'], {})

        rate_key = 'employee' if is_employee else 'employer'
        if age < 55:
            age_bracket = 'below_55'
        elif 55 <= age < 60:
            age_bracket = '55_to_60'
        elif 60 <= age < 65:
            age_bracket = '60_to_65'
        elif 65 <= age < 70:
            age_bracket = '65_to_70'
        else:
            age_bracket = 'above_70'
        return self.config.getdata(['cpf_contribution_rates', age_bracket, rate_key], 0.0)
    
     
    
    def calculate_cpf_contribution(self, is_employee: bool) -> float:
        """
        Calculates CPF contribution based on salary, age, and employment status.
        """
        capped_salary = min(self.salary, self.config.getdata(['salary_cap'], 0))

        # Determine the correct age bracket for contribution rates
        if self.age <= 55:
            age_bracket = 'below_55'
        elif 55 < self.age <= 60:
            age_bracket = '55_to_60'
        elif 60 < self.age <= 65:
            age_bracket = '60_to_65'
        elif 65 < self.age <= 70:
            age_bracket = '65_to_70'
        else:  # age > 70
            age_bracket = 'above_70'

        # Retrieve the contribution rate
        rate_key = 'employee' if is_employee else 'employer'
        rate = self.config.getdata(['cpf_contribution_rates', age_bracket, rate_key], 0.0)

        # Calculate the contribution
        contribution = capped_salary * rate
        if is_employee:
            self.employee_contribution = contribution
        else:
            self.employer_contribution = contribution

        return contribution

    def calculate_total_contributions(self) -> float:
        """
        Calculates the total CPF contributions (employee + employer) based on salary and age.
        Updates the `self.total_contribution` attribute.
        """
        # Calculate employee and employer contributions
        employee_contribution = self.calculate_cpf_contribution(is_employee=True)
        employer_contribution = self.calculate_cpf_contribution(is_employee=False)

        # Update the total contributions
        self.total_contribution = employee_contribution + employer_contribution
        #return self.total_contribution
        setattr(self, 'total_contribution', self.total_contribution)

    def calculate_cpf_payout(self) -> float:
        """Calculates the CPF payout amount based on age and retirement sum.
        only starts at the age of 67
        """
        payout_age = self.config.getdata(['cpf_payout_age'], 65)
        brs_payout = self.config.getdata(['retirement_sums', 'brs', 'payout'], 0.0)

        if self.age >= payout_age:
            return brs_payout
        else:
            return 0.0  # No payout before payout age

    def custom_serializer(self,obj):
        ''' called every month to save the log '''
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
        raise TypeError("Type not serializable")

    def calculate_loan_payment(self):
        """Calculates the loan payment amount based on the current loan balance.
        this is called every month
        """
        # Example logic for calculating loan payment
        if self._loan_balance > 0:
            # Assuming a fixed interest rate and term for simplicity
            interest_rate = 0.03

    def calculate_the_loan_amortization(self):
        """Calculates the loan amortization schedule.
        this is called every month
        """
        # Example logic for calculating loan amortization
        if self._loan_balance > 0:
            # Assuming a fixed interest rate and term for simplicity
            interest_rate = 0.03  # should be coming from the config in the future.
            term_years = 30  #should come from the config in the future 
            monthly_payment = self._loan_balance * (interest_rate / 12) / (1 - (1 + interest_rate / 12) ** (-term_years * 12))
            return monthly_payment
        else:
            return 0.0
        

    def loan_computation(self) -> float:
        """
        Calculates the loan payment amount based on the current loan balance and age.
        """
        if self._loan_balance <= 0:
            return 0.0

        # Determine the loan payment key based on age
        payment_key = 'year_1_2' if self.age < 24 else 'year_3'
        loan_payment_amount = self.config.getdata(['loan_payments', payment_key], 0.0)
        return loan_payment_amount

if __name__ == "__main__":
    try:
        config_loader = ConfigLoader('cpf_config.json')
        mycpf = CPFAccount(config_loader=config_loader)
        ages = [25, 55, 60, 65, 70, 75]
        for age in ages:
            mycpf.age = age
            mycpf.salary = 5000  # Example salary
            contribution = mycpf.calculate_cpf_contribution(is_employee=True)
            print(f"Age: {age}, Employee Contribution: {contribution}")

        # Test salary cap retrieval
            salary_cap = config_loader.getdata(['salary_cap'], 0)
            print(f"Salary Cap: {salary_cap}")

        # Test CPF contribution calculation
        
    

    except Exception as e:
        print(f"An error occurred: {e}")