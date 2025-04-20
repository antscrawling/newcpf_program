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
        self.inflow = {
            '_loan_balance': 0.0,
            '_excess_balance': 0.0,
            '_oa_balance': 0.0,
            '_ma_balance': 0.0,
            '_ra_balance': 0.0
        }
        self.outflow = {
            '_loan_balance': 0.0,
            '_excess_balance': 0.0,
            '_oa_balance': 0.0,
            '_sa_balance': 0.0,
            '_ma_balance': 0.0,
            '_ra_balance': 0.0
        }
        
        # Log saving setup
        self.log_queue = Queue()
        # Use the top-level worker function as the target
        # Pass only the queue and filename, which are picklable
        self.log_process = Process(target=_save_log_worker, args=(self.log_queue, 'logs.json'))
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
    def sa_balance(self):
        return self._sa_balance, self._sa_message

    @sa_balance.setter
    def sa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            # Ensure value is treated as float if data is not a tuple/list
            value, message = float(data), "no message"  # Assuming data should be numeric
        diff = value - self._sa_balance
        log_entry = {
            # Ensure current_date is set before logging
            'date': self.current_date if hasattr(self, 'current_date') else datetime.now(),
            'account': 'sa',  # Add account identifier
            'old_balance': self._sa_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'inflow' if diff > 0 else ('outflow' if diff < 0 else 'no change'),
            'message': f'sa-{message}-{diff:.2f}'  # Format diff for consistency
        }
        # self._sa_log.append(log_entry) # Optional: Keep in-memory log if needed
        self._sa_balance = value
        self._sa_message = message

        # Save the log entry using multiprocessing
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
        """Generate a date dictionary."""
        print("Warning: get_date_dict needs implementation in CPFAccount or be imported correctly.")
        from cpf_date_generator_v2 import generate_date_dict
        return generate_date_dict(start_date, end_date, birth_date)

    def update_balance(self, account: str, new_balance: float, message: str):
        """
        Sets the account balance to the specified new_balance and logs the change.
        The logged 'amount' reflects the difference from the old balance.
        """
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for update_balance: {account}")
            return # Or raise ValueError
        # Set the new balance using the provided value
        setattr(self, f"_{account}_balance", new_balance)
            

    def record_inflow(self, account: str, amount: float, message: str = None):
        """
        Records an inflow by adding the amount to the current balance
        and then calling update_balance to set the new value and log.
        """
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for record_inflow: {account}")
            return # Or raise ValueError

        if not isinstance(amount, (int, float)):
            print(f"Warning: Non-numeric inflow amount for {account}: {amount}. Skipping.")
            return
        if abs(amount) < 1e-9: return # No need to process zero inflow


        # Get current balance safely
        current_balance = getattr(self, f'_{account}_balance', 0.0)
        if not isinstance(current_balance, (float, int)):
            print(f"Warning: Current balance for {account} in record_inflow is not numeric ({current_balance}). Assuming 0.")
            current_balance = 0.0

        # Calculate the target new balance
        new_balance = current_balance + amount

        # Use update_balance to set the new value and handle logging
        # The message passed here describes the *reason* for the change (e.g., 'allocation', 'interest')
        self.update_balance(account=account, new_balance=new_balance, message=message or "inflow")

    def record_outflow(self, account: str, amount: float, message: str = None):
        """
        Records an outflow by subtracting the amount from the current balance
        and then calling update_balance to set the new value and log.
        """
        valid_accounts = ['oa', 'sa', 'ma', 'ra', 'loan', 'excess']
        if account not in valid_accounts:
            print(f"Error: Invalid account name for record_outflow: {account}")
            return # Or raise ValueError

        if not isinstance(amount, (int, float)):
            print(f"Warning: Non-numeric outflow amount for {account}: {amount}. Skipping.")
            return
        if abs(amount) < 1e-9: return # No need to process zero outflow

        if amount < 0:
             # Delegate negative outflow to inflow
             self.record_inflow(account, -amount, message or "negative_outflow_as_inflow")
             return

        # Get current balance safely
        current_balance = getattr(self, f'_{account}_balance', 0.0)
        if not isinstance(current_balance, (float, int)):
            print(f"Warning: Current balance for {account} in record_outflow is not numeric ({current_balance}). Assuming 0.")
            current_balance = 0.0

        # Calculate the target new balance
        new_balance = current_balance - amount

        # Use update_balance to set the new value and handle logging
        # The message passed here describes the *reason* for the change (e.g., 'loan_payment', 'transfer')
        self.update_balance(account=account, new_balance=new_balance, message=message or "outflow")

    def calculate_cpf_allocation(self, age: int, salary: float, account: str, config: ConfigLoader) -> float:
        """Calculates the allocation amount for a specific CPF account."""
        employee: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=True, config=config)
        employer: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=False, config=config)
        total_contribution = employee + employer
        alloc: float = 0.0

        # Use config.get() to access configuration values
        age_of_brs = config.get('age_of_brs', 55) # Added default for safety

        # Determine allocation based on age and account type
        if age <= age_of_brs:
            # Allocation for those below or at the BRS transfer age (typically 55)
            allocation_rates = config.get('allocation_below_55', {}) # Added default for safety
            if account in allocation_rates:
                 # Check if account is valid for this age group (oa, sa, ma)
                 alloc = allocation_rates.get(account, 0.0) * total_contribution # Added default for safety
            # Note: SA allocation stops at 55, RA starts.
            # This logic assumes the calling code handles which accounts are valid per age.
        else:
            # Allocation for those above the BRS transfer age
            allocation_rates = config.get('allocation_above_55', {}) # Added default for safety
            if account in allocation_rates:
                 # Check if account is valid for this age group (oa, ra, ma)
                 alloc = allocation_rates.get(account, 0.0) * total_contribution # Added default for safety

        return alloc

    def apply_interest(self, age: int):
        """Apply interest to all CPF accounts at the end of the year."""
        interest_rates = self.config.get('interest_rates', {})
        extra_interest = self.config.get('extra_interest', {})

        # Base interest rates
        oa_rate = interest_rates.get('oa_below_55', 2.5) if age < 55 else interest_rates.get('oa_above_55', 4.0)
        sa_rate = interest_rates.get('sa', 4.0)
        ma_rate = interest_rates.get('ma', 4.0)
        ra_rate = interest_rates.get('ra', 4.0)

        # Apply interest to each account
        self.record_inflow('oa', self._oa_balance * (oa_rate / 100 / 12), 'interest')
        self.record_inflow('sa', self._sa_balance * (sa_rate / 100 / 12), 'interest')
        self.record_inflow('ma', self._ma_balance * (ma_rate / 100 / 12), 'interest')
        self.record_inflow('ra', self._ra_balance * (ra_rate / 100 / 12), 'interest')


    def transfer_to_ra(self,age,retirement_type: str):
      
        retirement_sum = 0.0
        rtype = ''
        match retirement_type: 
            case 'basic':
                rtype='brs'
            case 'full':
                rtype='frs'
            case 'enhanced':
                rtype='ers'
            case _:
                raise ValueError(f"Invalid retirement type: {retirement_type}. Must be 'basic', 'full', or 'enhanced'.")
 
        """Transfer funds from OA to RA."""
        # Check if the transfer is allowed based on age and other conditions
       
        retirement_dict = self.config.get('retirement_sums', {})
        type_dict = retirement_dict.get(rtype, {})
        retirement_sum = type_dict.get('amount' ,{}) 
        
        #transfer:
        self._excess_balance = self._sa_balance + self._oa_balance
        self._excess_balance -= self._loan_balance
        self._excess_balance -= retirement_sum
        self._oa_balance -= self._oa_balance
        self._sa_balance -= self._sa_balance
        self._ra_balance += retirement_sum
            # transfer funds
        self.record_inflow('ra', retirement_sum , f"Transfer to RA for {rtype}")
        self.record_outflow('oa',self._oa_balance, f"Transfer to RA for age 55")
        self.record_outflow('sa',self._sa_balance, f"Transfer to RA for age 55")
        self.record_inflow('excess',self._oa_balance+self._sa_balance, f"Transfer to RA for age 55")
        self.record_outflow('loan',self._loan_balance, f"Transfer to RA for age 55")
        self.record_outflow('excess',retirement_sum, f"Transfer to RA for age 55")
        self.record_outflow('excess',-self._loan_balance, f"Transfer to RA for age 55")
        
                                                
    
    def get_cpf_contribution_rate(self, age:int,is_employee:bool)-> float:
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
        """Calculates CPF contribution based on salary, age, and employment status."""
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

    def calculate_cpf_allocation(self, age: int, salary: float, account: str, config: dict) -> float:
        """Calculates the allocation amount for a specific CPF account."""
        employee: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=True, config=config)
        employer: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=False, config=config)
        total_contribution = employee + employer
        alloc: float = 0.0

        # Use config.get() to access configuration values
        age_of_brs = config.get('age_of_brs', 55) # Added default for safety

        # Determine allocation based on age and account type
        if age <= age_of_brs:
            # Allocation for those below or at the BRS transfer age (typically 55)
            allocation_rates = config.get('allocation_below_55', {}) # Added default for safety
            if account in allocation_rates:
                 # Check if account is valid for this age group (oa, sa, ma)
                 alloc = allocation_rates.get(account, 0.0) * total_contribution # Added default for safety
            # Note: SA allocation stops at 55, RA starts.
            # This logic assumes the calling code handles which accounts are valid per age.
        else:
            # Allocation for those above the BRS transfer age
            allocation_rates = config.get('allocation_above_55', {}) # Added default for safety
            if account in allocation_rates:
                 # Check if account is valid for this age group (oa, ra, ma)
                 alloc = allocation_rates.get(account, 0.0) * total_contribution # Added default for safety

        return alloc

    def calculate_cpf_payout(self, age: int) -> float:
        """Calculates the CPF payout amount based on age and retirement sum."""
        payout_age = self.config.get('cpf_payout_age', 65)  # Default payout age if not specified
        retirement_sums = self.config.get('retirement_sums', {})
        brs_info = retirement_sums.get('brs', {})
        brs_payout = brs_info.get('payout', 0.0)  # Default payout if not specified

        if age >= payout_age:
            return brs_payout
        else:
            return 0.0  # No payout before payout age

    def custom_serializer(self,obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
        raise TypeError("Type not serializable")


if __name__ == "__main__":
    # Example usage
    with CPFAccount(config) as cpf:
        # Example of setting balances
        config_loader = ConfigLoader('new_config.json')
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
        cpf.transfer_to_ra(age=age, retirement_type='basic')
        print(f'Balances after  {cpf._oa_balance=}, {cpf._sa_balance=}, {cpf._ma_balance=}, {cpf._ra_balance=}, {cpf._loan_balance=}, {cpf._excess_balance=}')