from datetime import datetime, timedelta
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from pprint import pprint
#from dateutility import  MyDateDictGenerator
import json
from import_config import get_the_config
from convert_date import MyDateTime
from collections import OrderedDict

# Load configuration
config = get_the_config()


globals().update({
    k: v if isinstance(v, list) and len(v) == 3 and all(isinstance(i, int) for i in v)
    else v
    for k, v in config.items()
})


# Updated CPFAccount class with parameterized logic

class CPFAccount:
    def __init__(self):
        self.current_date = datetime.now()
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

        self.basic_retirement_sum = 0.0
        
        self._loan_balance = 0.0
        self._loan_balance_log = []
        self._loan_message = ""
        
        
        self.inflow = {'loan_balance': 0.0,
                       'excess_balance': 0.0,
                       'oa_balance': 0.0,
                       'sa_balance': 0.0,
                       'ma_balance': 0.0,
                       'ra_balance': 0.0}
        self.outflow = {'loan_balance': 0.0,
                        'excess_balance': 0.0,
                        'oa_balance': 0.0,
                        'sa_balance': 0.0,
                        'ma_balance': 0.0,
                        'ra_balance': 0.0}

    @property
    def oa_balance(self):
        return (self._oa_balance, self._oa_message)

    @oa_balance.setter
    def oa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._oa_balance
        self._oa_log.append({
            'date': self.current_date,
            'amount': abs(diff),
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'oa-{message}-{diff}'
        })
        self._oa_balance = value
        self._oa_message = message

    @property
    def sa_balance(self):
        return ( self._sa_balance,self._sa_message)

    @sa_balance.setter
    def sa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._sa_balance
        self._sa_log.append({
            'date': self.current_date,
            'amount': abs(diff),
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'sa-{message}-{diff}'
        })
        self._sa_balance = value
        self._sa_message = message

    @property
    def ma_balance(self):
        return(  self._ma_balance,  self._ma_message)

    @ma_balance.setter
    def ma_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._ma_balance
        self._ma_log.append({
            'date': self.current_date,
            'amount': abs(diff),
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'ma-{message}-{diff}'
        })
        self._ma_balance = value
        self._ma_message = message

    @property
    def ra_balance(self):
        return ( self._ra_balance, self._ra_message)

    @ra_balance.setter
    def ra_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = "no message"
        diff = value - self._ra_balance
        self._ra_log.append({
            'date': self.current_date,
            'amount': abs(diff),
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'ra-{message}-{diff}'
        })
        self._ra_balance = value
        self._ra_message = message

    @property
    def excess_balance(self):
        return (self._excess_balance, self._excess_message)

    @excess_balance.setter
    def excess_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._excess_balance
        self._excess_balance_log.append({
            'date': self.current_date,
            'amount': abs(diff),
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'excess-{message}-{diff}'
        })
        self._excess_balance = value
        self._excess_message = message

    @property
    def loan_balance(self):
        return   ( self._loan_balance, self._loan_message)

    @loan_balance.setter
    def loan_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._loan_balance
        self._loan_balance_log.append({
            'date': self.current_date,
            'amount': abs(diff),
            'type': 'outflow' if diff > 0 else 'inflow',
            'message': f'loan-{message}-{diff}'
        })
        self._loan_balance = value
        self._loan_message = message



    def update_balance(self, account: str, change: float, message: str = None):
        """Wrapper function to update account balances and log changes."""
        if not isinstance(change, (int, float)):
            raise ValueError(f"Expected change to be a float or int, got {type(change)}")
        current_balance = getattr(self, f'{account}_balance')  # Get the current balance
        new_balance = (current_balance[0] + change, message)  # Update balance and include message
        setattr(self, f'{account}_balance', new_balance)  # Set the updated balance
        
        
    def record_inflow(self, account: str, amount: float, message: str = None):
        """Record inflow for a specific account."""
        if not isinstance(amount, (int, float)):
            raise ValueError(f"Expected amount to be a float or int, got {type(amount)}")
        self.inflow[f'{account}_balance'] += float(amount)
        self.update_balance(account=f"{account}", change=amount, message=message)
        
    def record_outflow(self, account: str, amount: float, message: str = None):
        """Record outflow for a specific account."""
        if not isinstance(amount, (int, float)):
            raise ValueError(f"Expected amount to be a float or int, got {type(amount)}")
        self.outflow[f'{account}_balance'] += float(amount)
        self.update_balance(account=f'{account}', change=-amount, message=message)

            
    def get_age(self, current_date:datetime) -> int:
        # Calculate the age based on the current date and birth date
        return DATE_DICT.get(current_date.strftime("%b-%Y"))['age']
    
    def get_cpf_contribution_rate(self, age:int,is_employee:bool)-> float:
        if age < 55:
            employee_rate : float = CPF_CONTRIBUTION_RATES["below_55"]["employee"]
            employer_rate : float = CPF_CONTRIBUTION_RATES["below_55"]["employer"]
        elif 55 <= age < 60:
            employee_rate : float  = CPF_CONTRIBUTION_RATES["55_to_60"]["employee"]
            employer_rate : float  = CPF_CONTRIBUTION_RATES["55_to_60"]["employer"]
        elif 60 <= age < 65:
            employee_rate : float  = CPF_CONTRIBUTION_RATES["60_to_65"]["employee"]
            employer_rate : float  = CPF_CONTRIBUTION_RATES["60_to_65"]["employer"]
        elif 65 <= age < 70:
            employee_rate : float = CPF_CONTRIBUTION_RATES["65_to_70"]["employee"]
            employer_rate : float = CPF_CONTRIBUTION_RATES["65_to_70"]["employer"]
        else:
            employee_rate : float = CPF_CONTRIBUTION_RATES["above_70"]["employee"]
            employer_rate : float = CPF_CONTRIBUTION_RATES["above_70"]["employer"]
        if is_employee:
            return employee_rate 
        else :
            return employer_rate
    
     
    
    def calculate_cpf_contribution(self, salary:float,age:int, is_employee:bool) -> float:
        capped_salary : float = min(salary, SALARY_CAP)
        employee_rate : float = self.get_cpf_contribution_rate(age=age,is_employee=True)    
        employer_rate : float = self.get_cpf_contribution_rate(age=age,is_employee=False)
        employee_contribution = capped_salary * employee_rate
        employer_contribution = capped_salary * employer_rate
        if is_employee:
           
            return employee_contribution 
        else:
            return employer_contribution
       
    def calculate_cpf_allocation(self, age:int,salary:float,account:str)-> float:
        employee : float  = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=True)
        employer : float  = self.calculate_cpf_contribution(salary=salary, age=age, is_employee=False)
        alloc: float = 0.0  # Initialize alloc with a default value
        # Determine allocation based on age and account type                                   
        if account in ['oa', 'ma','sa'] and age < AGE_FOR_BRS_TRANSFER['age']:
           
                # This is July month of 2029.  get the below 55 rate
                alloc = SALARY_ALLOCATION_BELOW_55[account] * (employee + employer)
        else:
                alloc = SALARY_ALLOCATION_ABOVE_55[account] * (employee + employer)
        return alloc
                                                                                                                                                                                                                                                                    
    def apply_interest(self, age):
        oa_interest_rate = OA_INTEREST_RATE_BELOW_55 if age < AGE_FOR_BRS_TRANSFER['age'] else OA_INTEREST_RATE_ABOVE_55
        interest_rates = [oa_interest_rate, SA_INTEREST_RATE, RA_INTEREST_RATE, MA_INTEREST_RATE]
        accounts = ['oa', 'sa', 'ra', 'ma']
        balances = [self.oa_balance, self.sa_balance, self.ra_balance, self.ma_balance]

        for account, balance, rate in zip(accounts, balances, interest_rates):
            self.record_inflow(account, balance[0] * rate / 100, message=f'{account}_interest')

        self.apply_extra_interest(age)
        
        
    def apply_extra_interest(self, age):
        combined_balance = min(self.oa_balance[0], 20_000) + self.sa_balance[0] + self.ma_balance[0]
        if age >= AGE_FOR_BRS_TRANSFER['age']:
            combined_balance += self.ra_balance[0]

        if combined_balance >= 30_000:
            first_30k = min(combined_balance, 30_000)
            extra_interest_first_30k = first_30k * EXTRA_INTEREST_FIRST_30K_ABOVE_55 / 100
            self.record_inflow(account='ra', amount=extra_interest_first_30k, message='extra_first30k_interest')

        if combined_balance >= 60_000:
            extra_interest_next_30k = (combined_balance - 30_000) * EXTRA_INTEREST_NEXT_30K_ABOVE_55 / 100
            self.record_inflow(account='ra', amount=extra_interest_next_30k, message='extra_next30k_interest')

   
   

    def calculate_cpf_payout(self, age):
        return CPF_PAYOUT_AMOUNT_BRS if age >= AGE_FOR_CPF_PAYOUT else 0

        
    def transfer_funds(self, from_account: str, to_account: str, amount: float, is_total_amount: bool = False, message: str = None):
        """Transfer funds from one account to another."""
        if is_total_amount:
            amount = getattr(self, f'{from_account}_balance')[0]  # Extract only the balance (first element of the tuple)
        self.record_outflow(from_account, amount, message=f'transfer-{from_account}-{amount}')
        self.record_inflow(to_account, amount, message=f'transfer-{to_account}-{amount}')
        
        

    def custom_serializer(self,obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
        raise TypeError("Type not serializable")

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

# Updated generate_cpf_projection function
def generate_cpf_projection():
    cpf = CPFAccount()
    cpf.oa_balance = 167892.11,'initial'
    cpf.sa_balance = 253163.35,'initial'
    cpf.ma_balance = 72952.37,'initial'
    cpf.ra_balance = 0.00,'initial'
    cpf.excess_balance = 0.00,'initial'
    cpf.loan_balance = 251101.00,'initial'
    cpf.basic_retirement_sum = BASIC_RETIREMENT_SUM['amount']

    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    records = []
    for month in range(1, 300):
        age = cpf.get_age(current_date=cpf.current_date)

        # Loan payment logic
        if cpf.current_date.year <= 2029 and cpf.current_date.month < 7:
            loan_payment = LOAN_PAYMENT_YEAR_1_2 if month < 24 else LOAN_PAYMENT_YEAR_3 if month < 36 else LOAN_PAYMENT_YEAR_4_BEYOND
            loan_payment = min(loan_payment, cpf.loan_balance[0])
            cpf.loan_balance = (calculate_loan_balance(cpf.loan_balance[0], interest_rate=2.5, monthly_payment=loan_payment, months=1), "loan_payment")

        # CPF allocation logic
        for account in ['oa', 'ma', 'sa'] if age < AGE_FOR_BRS_TRANSFER['age'] else ['oa', 'ma', 'ra']:
            allocation = cpf.calculate_cpf_allocation(age=age, salary=SALARY, account=account)
            cpf.record_inflow(account=account, amount=allocation, message=f'allocation_{account}')

        # Apply interest at the end of the year
        if cpf.current_date.month == 12:
            cpf.apply_interest(age=age)

        # CPF payout
        cpf_payout = cpf.calculate_cpf_payout(age=age)
        cpf.record_inflow(account='excess', amount=cpf_payout, message=f'cpf_payout_{age}')

        # Display balances
        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{cpf.sa_balance[0]:<15,.2f}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{cpf_payout:<12,.2f}")

        # Save record for JSON
#        records.append({
#            "date": cpf.custom_serializer(cpf.current_date),
#            "age": age,
#            "oa_balance": cpf.oa_balance,
#            "sa_balance": cpf.sa_balance,
#            "ma_balance": cpf.ma_balance,
#            "ra_balance": cpf.ra_balance,
#            "loan_balance": cpf.loan_balance,
#            "excess_balance": cpf.excess_balance,
#        })

        # Move to the next month
        cpf.current_date += timedelta(days=30)

  ## Save records to JSON
  #with open("cpf_projection.json", "w") as json_file:
  #    json.dump(records, json_file, indent=4, default=cpf.custom_serializer)

  #print("Projection saved to cpf_projection.json")


def calculate_loan_balance(principal: float, interest_rate: float, monthly_payment: float, months: int) -> float:
    for _ in range(months):
        interest = principal * (interest_rate / 12 / 100)
        principal = principal + interest - monthly_payment
        if principal <= 0:
            return 0.0
    return principal


if __name__ == "__main__":
    generate_cpf_projection()