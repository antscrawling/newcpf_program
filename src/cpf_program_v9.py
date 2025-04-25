import atexit
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from pprint import pprint
#from dateutility import  MyDateDictGenerator
import json
from cpf_config_loader_v2 import ConfigLoader
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

        # Account balances and logs
        self._oa_balance = 0.0
        self._oa_log = []
        self._oa_message = ""

        self._sa_balance = 0.0
        self._sa_log = []
        self._sa_message = ""

        self._ma_balance = 0.0
        self._ma_log = []
        self._ma_message = ""

        self._ra_balance = 0.0
        self._ra_log = []
        self._ra_message = ""

        self._excess_balance = 0.0
        self._excess_balance_log = []
        self._excess_message = ""

        self._loan_balance = 0.0
        self._loan_balance_log = []
        self._loan_message = ""       
        
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
            'amount': diff,
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
            'amount': diff,
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
            'amount': diff,
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
            'amount': diff,
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'loan-{self.message}-{diff:.2f}'
        }
        self._loan_balance = value.__round__(2)
        self._loan_message = self.message
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

    def calculate_cpf_allocation(self, age: int, salary: float, account: str, config: ConfigLoader) -> float:
        """Calculates the allocation amount for a specific CPF account.
                   "allocation_below_55": {
               "oa": 0.23,
               "sa": 0.06,
               "ma": 0.08
           },
           "allocation_above_55": {
               "oa": 0.115,
               "ra": 0.105,
               "ma": 0.075
           },
        """
        employee: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=True, config=config)
        employer: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=False, config=config)
        total_contribution = employee + employer
        alloc: float = 0.0

        # Use config.get() to access configuration values
        age_of_brs = config.get('age_of_brs', 55) # Added default for safety

        # Determine allocation based on age and account type
        if age < age_of_brs: # Use '<' instead of '<='
            # Allocation for those below the BRS transfer age (typically 55)
            allocation_rates = config.get('allocation_below_55', {}) # Added default for safety
            if account in allocation_rates:
                 # Check if account is valid for this age group (oa, sa, ma)
                 alloc = allocation_rates.get(account, 0.0) * total_contribution # Added default for safety
            # Note: SA allocation stops at 55, RA starts.
            # This logic assumes the calling code handles which accounts are valid per age.
        else: # This now correctly handles age >= age_of_brs (e.g., age >= 55)
            # Allocation for those at or above the BRS transfer age
            allocation_rates = config.get('allocation_above_55', {}) # Added default for safety
            if account in allocation_rates:
                 # Check if account is valid for this age group (oa, ra, ma)
                 alloc = allocation_rates.get(account, 0.0) * total_contribution # Added default for safety

        return alloc

    def apply_interest(self, age: int):
        """Apply interest to all CPF accounts at the end of the year.
        this is caloled every December - 12 of every year
        """

        interest_rates = self.config.get('interest_rates', {})
        extra_interest = self.config.get('extra_interest', {})

        # Base interest rates
        oa_rate = interest_rates.get('oa_below_55', 2.5) if age < 55 else interest_rates.get('oa_above_55', 4.0)
        sa_rate = interest_rates.get('sa', 4.0)
        ma_rate = interest_rates.get('ma', 4.0)
        ra_rate = interest_rates.get('ra', 4.0)

        # Apply interest to each account
      # self.record_inflow('oa', self._oa_balance * (oa_rate / 100 / 12), 'interest')
      # self.record_inflow('sa', self._sa_balance * (sa_rate / 100 / 12), 'interest')
      # self.record_inflow('ma', self._ma_balance * (ma_rate / 100 / 12), 'interest')
      # self.record_inflow('ra', self._ra_balance * (ra_rate / 100 / 12), 'interest')
        return (self._oa_balance * (oa_rate / 100 / 12),
                self._sa_balance * (sa_rate / 100 / 12),
                self._ma_balance * (ma_rate / 100 / 12),
                self._ra_balance * (ra_rate / 100 / 12))
             
             
             



  # def transfer_to_ra(self,age,retirement_type: str):
  #     '''Function to transfer funds only at age 55 month.  only called once in the program '''
  #     retirement_sum = 0.0
  #     rtype = ''
  #     match retirement_type: 
  #         case 'basic':
  #             rtype='brs'
  #         case 'full':
  #             rtype='frs'
  #         case 'enhanced':
  #             rtype='ers'
  #         case _:
  #             raise ValueError(f"Invalid retirement type: {retirement_type}. Must be 'basic', 'full', or 'enhanced'.")
 
  #     """Transfer funds from OA to RA."""
  #     # Check if the transfer is allowed based on age and other conditions
  #    
  #     retirement_dict = self.config.get('retirement_sums', {})
  #     type_dict = retirement_dict.get(rtype, {})
  #     retirement_sum = type_dict.get('amount' ,{}) 
  #     
  #     #transfer:
  #         # transfer funds
  #     self.record_inflow('excess',self._oa_balance+self._sa_balance, f"Transfer to RA for age 55")
  #     self.record_outflow('excess',retirement_sum, f"Transfer to RA for age 55")
  #     self.record_outflow('excess',self._loan_balance, f"Transfer to RA for age 55")
  #     
  #     self.record_inflow('ra', retirement_sum , f"Transfer to RA for {rtype}")
  #     self.record_outflow('oa',self._oa_balance, f"Transfer to RA for age 55")
  #     self.record_outflow('sa',self._sa_balance, f"Transfer to RA for age 55")        
  #     self.record_outflow('loan',self._loan_balance, f"Transfer to RA for age 55")
        
        
                                                
    
    def get_cpf_contribution_rate(self, age:int,is_employee:bool)-> float:
        ''' this is called in different age group 
                "cpf_contribution_rates": {
            "below_55": {
                "employee": 0.2,
                "employer": 0.17
            },
            "55_to_60": {
                "employee": 0.15,
                "employer": 0.14
            },
            "60_to_65": {
                "employee": 0.09,
                "employer": 0.1
            },
            "65_to_70": {
                "employee": 0.075,
                "employer": 0.085
            },
            "above_70": {
                "employee": 0.05,
                "employer": 0.075
            }
        '''
        cont_dict = self.config.get('cpf_contribution_rates', {})
        d_below_55 = cont_dict.get('below_55', {})
        
        d__55to60  = cont_dict.get('55_to_60', {})
        d_60to65 = cont_dict.get('60_to_65', {})
        d_65to70 = cont_dict.get('65_to_70', {})
        
        
        # Use config.get() to access configuration values
        if age < 55:
            employee_rate : float =  d_below_55.get('employee',{}) 
            employer_rate : float =  d_below_55.get('employer',{})
        elif 55 <= age < 60:#
            employee_rate : float  = d__55to60.get('employee',{})
            employer_rate : float  = d__55to60.get('employer',{})
        elif 60 <= age < 65:#
            employee_rate : float  =  d_60to65.get('employee',{})
            employer_rate : float  =  d_60to65.get('employer',{})
        elif 65 <= age < 70:
            employee_rate : float =  d_65to70.get('employee',{}) 
            employer_rate : float =  d_65to70.get('employer',{}) 
        else:
            employee_rate : float = 0.0
            employer_rate : float =    0.0
        if is_employee:
            return employee_rate 
        else :
            return employer_rate
    
     
    
    def calculate_cpf_contribution(self, salary: float, age: int, is_employee: bool, config: ConfigLoader) -> float:
        """Calculates CPF contribution based on salary, age, and employment status.
        "cpf_contribution_rates": {
    "below_55": {
        "employee": 0.2,
        "employer": 0.17
    },
    "55_to_60": {
        "employee": 0.15,
        "employer": 0.14
    },
    "60_to_65": {
        "employee": 0.09,
        "employer": 0.1
    },
    "65_to_70": {
        "employee": 0.075,
        "employer": 0.085
    },
    "above_70": {
        "employee": 0.05,
        "employer": 0.075
    }
        """
        # Use config.get() to access configuration values
        capped_salary: float = min(salary, config.get('salary_cap', 0)) # Added default for safety

        rates = config.get('cpf_contribution_rates', {}) # Added default for safety

        # Determine the correct age bracket for contribution rates
        if age <= 55:
            age_bracket = 'below_55'
        elif 55 < age <= 60:
            age_bracket = '55_to_60'
        elif 60 < age <= 65:
            age_bracket = '60_to_65'
        elif 65 < age <= 70:
            age_bracket = '65_to_70'
        else: # age > 70
            age_bracket = 'above_70'

        contribution_rate_info = rates.get(age_bracket, {}) # Added default for safety

        if is_employee:
            rate = contribution_rate_info.get('employee', 0.0) # Added default for safety
            contribution = capped_salary * rate
        else: # Employer contribution
            rate = contribution_rate_info.get('employer', 0.0) # Added default for safety
            contribution = capped_salary * rate

        return contribution

    def calculate_cpf_payout(self, age: int) -> float:
        """Calculates the CPF payout amount based on age and retirement sum.
        only starts at the age of 67
        """
        payout_age = self.config.get('cpf_payout_age', 65)  # Default payout age if not specified
        retirement_sums = self.config.get('retirement_sums', {})
        brs_info = retirement_sums.get('brs', {})
        brs_payout = brs_info.get('payout', 0.0)  # Default payout if not specified

        if age >= payout_age:
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
        

    def loan_computation(self):
        ''' this is called every month to calculate the loan payment '''
        '''" Calculate the loan payment to be deducted from the outstanding loan every month
        loan_payments": {
           "year_1_2": 1687.39,
           "year_3": 1782.27,
           "year_4_beyond": 1817.49
        ,'''
        if self._loan_balance <= 0:
            return 0.0
        else : 
            theyear = self.current_date.year - self.start_date.year
            if theyear < 3:
                return self._loan_balance * 0.03 / 12
            else:
                return self._loan_balance * 0.03 / 12
        loan_payments = self.config.get(['loan_payments','year_1_2'], {}) #1687.39
        payment_key = 'year_1_2' if age < 24 else 'year_3'
        loan_payment_amount = float(loan_payments.get(payment_key, 0.0))
        return loan_payment_amount

if __name__ == "__main__":
    # Example usage
    with CPFAccount(config) as cpf:
        # Example of setting balances
        config_loader = ConfigLoader('cpf_config.json')
        start_date = config_loader.get('start_date',{})
        end_date = config_loader.get('end_date',{})
        birth_date = config_loader.get('birth_date',{})
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        salary = config_loader.get('salary',{})
        cpf.current_date = date(2029,7,1)
        
        
        
        
        age = 55
        cpf._oa_balance = 106500
        cpf._sa_balance = 60
        cpf._ma_balance = 30
        cpf._ra_balance = 40
        cpf._loan_balance = 50
        cpf._excess_balance = 0
        print(isinstance(cpf.start_date , datetime))
        print(f'Balances before {cpf._oa_balance=}, {cpf._sa_balance=}, {cpf._ma_balance=}, {cpf._ra_balance=}, {cpf._loan_balance=}, {cpf._excess_balance=}')
       # cpf.transfer_to_ra(age=age, retirement_type='basic')
        print(f'Balances after  {cpf._oa_balance=}, {cpf._sa_balance=}, {cpf._ma_balance=}, {cpf._ra_balance=}, {cpf._loan_balance=}, {cpf._excess_balance=}')