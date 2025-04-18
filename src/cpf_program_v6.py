from datetime import datetime, timedelta
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from pprint import pprint
#from dateutility import  MyDateDictGenerator
import json
from cpf_config_loader_v2 import ConfigLoader
from reconfigure_date import MyDateTime

from collections import OrderedDict
import inspect
from multiprocessing import Process, Queue

# Load configuration
config = ConfigLoader('cpf_config.json')


class CPFAccount:
    def __init__(self, config_loader: ConfigLoader):  # Accept config_loader
        self.config = config_loader  # Store the config_loader instance
        self.current_date = datetime.now()

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

        self.basic_retirement_sum = 0.0

        self.inflow = {
            'loan_balance': 0.0,
            'excess_balance': 0.0,
            'oa_balance': 0.0,
            'sa_balance': 0.0,
            'ma_balance': 0.0,
            'ra_balance': 0.0
        }
        self.outflow = {
            'loan_balance': 0.0,
            'excess_balance': 0.0,
            'oa_balance': 0.0,
            'sa_balance': 0.0,
            'ma_balance': 0.0,
            'ra_balance': 0.0
        }

        # Log saving setup
        self.log_queue = Queue()
        self.log_process = Process(target=self._save_log_worker, args=(self.log_queue, 'logs.json'))
        self.log_process.start()

    def _save_log_worker(self, queue, filename):
        """Worker process to save logs to a file."""
        with open(filename, 'a') as file:
            while True:
                log_entry = queue.get()
                if log_entry == "STOP":
                    break
                file.write(json.dumps(log_entry, default=self.custom_serializer) + '\n')

    def save_log_to_file(self, log_entry):
        """Send log entry to the worker process."""
        self.log_queue.put(log_entry)

    def close_log_writer(self):
        """Stop the log writer process."""
        self.log_queue.put("STOP")
        self.log_process.join()

    def custom_serializer(self, obj):
        """Custom serializer for non-serializable objects like datetime."""
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        raise TypeError("Type not serializable")

    @property
    def oa_balance(self):
        return self._oa_balance, self._oa_message

    @oa_balance.setter
    def oa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._oa_balance
        log_entry = {
            'date': self.current_date,
            'old_balance': self._oa_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'oa-{message}-{diff}'
        }
        self._oa_log.append(log_entry)
        self._oa_balance = value
        self._oa_message = message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    @property
    def sa_balance(self):
        return self._sa_balance, self._sa_message

    @sa_balance.setter
    def sa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._sa_balance
        log_entry = {
            'date': self.current_date,
            'old_balance': self._sa_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'sa-{message}-{diff}'
        }
        self._sa_log.append(log_entry)
        self._sa_balance = value
        self._sa_message = message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    @property
    def ma_balance(self):
        return self._ma_balance, self._ma_message

    @ma_balance.setter
    def ma_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._ma_balance
        log_entry = {
            'date': self.current_date,
            'old_balance': self._ma_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'ma-{message}-{diff}'
        }
        self._ma_log.append(log_entry)
        self._ma_balance = value
        self._ma_message = message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    @property
    def ra_balance(self):
        return self._ra_balance, self._ra_message

    @ra_balance.setter
    def ra_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._ra_balance
        log_entry = {
            'date': self.current_date,
            'old_balance': self._ra_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'ra-{message}-{diff}'
        }
        self._ra_log.append(log_entry)
        self._ra_balance = value
        self._ra_message = message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    @property
    def excess_balance(self):
        return self._excess_balance, self._excess_message

    @excess_balance.setter
    def excess_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._excess_balance
        log_entry = {
            'date': self.current_date,
            'old_balance': self._excess_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'excess-{message}-{diff}'
        }
        self._excess_balance_log.append(log_entry)
        self._excess_balance = value
        self._excess_message = message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    @property
    def loan_balance(self):
        return self._loan_balance, self._loan_message

    @loan_balance.setter
    def loan_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._loan_balance
        log_entry = {
            'date': self.current_date,
            'old_balance': self._loan_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'outflow' if diff > 0 else 'inflow',
            'message': f'loan-{message}-{diff}'
        }
        self._loan_balance_log.append(log_entry)
        self._loan_balance = value
        self._loan_message = message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    def close(self):
        """Ensure the log writer process is properly closed."""
        self.close_log_writer()

    def set_balance(self, account_type, amount, metadata):
        setattr(self, f"{account_type}_balance", (amount, metadata))

    def update_balance(self, account: str, change: float, message: str = None):
        """Wrapper function to update account balances and log changes."""
        if not isinstance(change, (int, float)):
            raise ValueError(f"Expected change to be a float or int, got {type(change)}")
        current_balance = getattr(self, f'{account}_balance')  # Get the current balance
        new_balance = (current_balance[0] + change, message)  # Update balance and include message
        setattr(self, f'{account}_balance', new_balance)  # Set the updated balance

    def transfer_to_ra(self):
        """Transfer OA and SA balances to RA at age 55, up to the Basic Retirement Sum (BRS).
        The remaining amount is transferred to the Excess Balance."""
        self._excess_balance += self._oa_balance
        self._excess_balance += self._sa_balance
        self._ra_balance += config.get('retirement_sums', {}).get('brs', {}).get('amount', 0)
        self._excess_balance -= self._loan_balance

        self.update_balance('excess', self.oa_balance[0], 'transfer_oa_to_excess')
        self.update_balance('excess', self.sa_balance[0], 'transfer_sa_to_excess')
        self.update_balance('excess', self.loan_balance[0], 'loan_fully_paid')
        self.update_balance('ra', self.basic_retirement_sum, 'transfer_to_ra')
        self.update_balance('loan', -self.loan_balance[0], 'loan_fully_paid')

    def calculate_cpf_allocation(self, age: int, salary: float, account: str, config: ConfigLoader) -> float:
        employee: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=True, config=config)
        employer: float = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=False, config=config)
        alloc: float = 0.0  # Initialize alloc with a default value
        # Determine allocation based on age and account type                                   
        if account in ['oa', 'ma', 'sa'] and age < config.get('age_of_brs'):
            alloc = config.get('allocation_below_55')[account] * (employee + employer)
        else:
            alloc = config.get('allocation_above_55')[account] * (employee + employer)
        return alloc

    def get_property_attributes(cls):
        return [
        name for name, value in inspect.getmembers(cls)
        if isinstance(value, property)
    ]

    def get_age(self, current_date: datetime) -> int:
        """Calculate the age based on the current date and birth date."""
        birth_date = self.config.get('birth_date')
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
        return current_date.year - birth_date.year - (
            (current_date.month, current_date.day) < (birth_date.month, birth_date.day)
        )
    
    def get_cpf_contribution_rate(self, age:int,is_employee:bool)-> float:
        if age < 55:
            employee_rate : float = config["below_55"]["employee"]
            employer_rate : float = config["below_55"]["employer"]
        elif 55 <= age < 60:
            employee_rate : float  = config["55_to_60"]["employee"]
            employer_rate : float  = config["55_to_60"]["employer"]
        elif 60 <= age < 65:
            employee_rate : float  = config["60_to_65"]["employee"]
            employer_rate : float  = config["60_to_65"]["employer"]
        elif 65 <= age < 70:
            employee_rate : float = config["65_to_70"]["employee"]
            employer_rate : float = config["65_to_70"]["employer"]
        else:
            employee_rate : float = config["above_70"]["employee"]
            employer_rate : float = config["above_70"]["employer"]
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
        self.update_balance('oa', self._oa_balance * (oa_rate / 100 / 12), 'interest')
        self.update_balance('sa', self._sa_balance * (sa_rate / 100 / 12), 'interest')
        self.update_balance('ma', self._ma_balance * (ma_rate / 100 / 12), 'interest')
        self.update_balance('ra', self._ra_balance * (ra_rate / 100 / 12), 'interest')

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

    def get_date_dict(self, start_date=None, birth_date=None, end_date=None) -> dict:
        """
        Returns a dictionary of the form:
        {
            'Apr-2025': {'age': 50},
            'May-2025': {'age': 50},
            ...
        }
        """
        if isinstance(start_date, list):
            start_date = datetime(start_date[0], start_date[1], start_date[2])
        if isinstance(birth_date, list):
            birth_date = datetime(birth_date[0], birth_date[1], birth_date[2])
        if isinstance(end_date, list):
            end_date = datetime(end_date[0], end_date[1], end_date[2])

        total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1

        date_dict = OrderedDict(
            (
                (date := start_date + relativedelta(months=i)).strftime('%b-%Y'),
                {
                    "age": date.year - birth_date.year - (
                        1 if (date.month < birth_date.month or (date.month == birth_date.month and date.day < birth_date.day)) else 0
                    )
                }
            )
            for i in range(total_months)
        )

        return date_dict


def calculate_loan_balance(principal: float, interest_rate: float, monthly_payment: float, months: int) -> float:
    for _ in range(months):
        interest = principal * (interest_rate / 12 / 100)
        principal = principal + interest - monthly_payment
        if principal <= 0:
            return 0.0
    return principal


if __name__ == "__main__":
    # Initialize CPFAccount
    cpf = CPFAccount(config_loader=ConfigLoader('new_config.json'))

    # Update balances
    cpf.sa_balance = (1000, "Initial SA balance")
    cpf.oa_balance = (2000, "Initial OA balance")

    # Perform some operations
    cpf.sa_balance = (1500, "SA inflow")
    cpf.oa_balance = (1800, "OA outflow")

    # Close the log writer process explicitly (optional, as atexit will handle it)
    cpf.close()

