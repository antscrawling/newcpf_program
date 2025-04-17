from datetime import datetime, timedelta
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from pprint import pprint
from dateutility_copy import  MyDateDictGenerator
import json


# Configuration Parameters
START_DATE = datetime(2025, 4, 1)
END_DATE = datetime(2060, 7, 31)
BIRTH_DATE = datetime(1974, 7, 6)
OA_INTEREST_RATE_BELOW_55 = 2.5
OA_INTEREST_RATE_ABOVE_55 = 4.0
SA_INTEREST_RATE = 4.0
MA_INTEREST_RATE = 4.0
RA_INTEREST_RATE = 4.0
EXTRA_INTEREST_BELOW_55 = 1.0
EXTRA_INTEREST_FIRST_30K_ABOVE_55 = 2.0
EXTRA_INTEREST_NEXT_30K_ABOVE_55 = 1.0
BASIC_RETIREMENT_SUM = {'amount': 106_500, 'payout':930}
FULL_RETIREMENT_SUM = { 'amount':213_000, 'payout': 1_670}
ENHANCED_RETIREMENT_SUM = {'amount':426_000,'payout':3_300}
AGE_FOR_BRS_TRANSFER = {'age':55, 'month': BIRTH_DATE.month, 'year':2029}
AGE_FOR_CPF_PAYOUT = 67
CPF_PAYOUT_AMOUNT_BRS= BASIC_RETIREMENT_SUM['payout']
CPF_PAYOUT_AMOUNT_FRS= FULL_RETIREMENT_SUM['payout']
CPF_PAYOUT_AMOUNT_ERS= ENHANCED_RETIREMENT_SUM['payout']
CPF_PAYMENT_AMOUNT = BASIC_RETIREMENT_SUM['payout']
SALARY_CAP = 7400
SALARY_ALLOCATION_BELOW_55 = {"oa": 0.23, "sa": 0.06, "ma": 0.08}
SALARY_ALLOCATION_ABOVE_55 = {"oa": 0.115, "ra": 0.105, "ma": 0.075}
SALARY = float(input("Enter your monthly salary: "))
LOAN_PAYMENT_YEAR_1_2 = 1687.39
LOAN_PAYMENT_YEAR_3 = 1782.27
LOAN_PAYMENT_YEAR_4_BEYOND = 1817.49
DATE_DICT_GENERATOR = MyDateDictGenerator()
DATE_DICT = DATE_DICT_GENERATOR.get_date_dict(start_date=START_DATE, birth_date=BIRTH_DATE, end_date=END_DATE)
# DATE_DICT = {'Apr-2025':{'age':50}}
MONTH : int = 0
CPF_CONTRIBUTION_RATES= {
    "below_55" : {"employee": 0.20,  "employer": 0.17  },
     "55_to_60": {"employee": 0.15,  "employer": 0.14  },
     "60_to_65": {"employee": 0.09,  "employer": 0.10  },
     "65_to_70": {"employee": 0.075, "employer": 0.085 },
     "above_70": {"employee": 0.05,  "employer": 0.075 }
}



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
            value, message = data, "no message"
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
        [self.record_inflow(account, balance[0] * rate / 100) for account, balance, rate in zip(['oa', 'sa', 'ra', 'ma'], [self.oa_balance, self.sa_balance, self.ra_balance, self.ma_balance], [oa_interest_rate, SA_INTEREST_RATE, RA_INTEREST_RATE, MA_INTEREST_RATE])]
      
        self.apply_extra_interest(age)
        
        
    def apply_extra_interest(self, age):
        if age < AGE_FOR_BRS_TRANSFER['age']:
            combined_balance = min(self.oa_balance[0], 20_000) + self.sa_balance[0] + self.ma_balance[0]
            if combined_balance >= 60_000:
                extra_interest = combined_balance * EXTRA_INTEREST_BELOW_55 / 100
            else:
                extra_interest = 0
            #self.oa_balance += extra_interest
            self.record_inflow(account='oa', amount=extra_interest, message='extra_first30k_interest')
        else:
            combined_balance = min(self.oa_balance[0], 20_000) + self.sa_balance[0] + self.ma_balance[0] + self.ra_balance[0]
            if combined_balance >= 30_000:
                first_30k = min(combined_balance, 30_000)
                extra_interest_first_30k = first_30k * EXTRA_INTEREST_FIRST_30K_ABOVE_55 / 100
              # self.ra_balance += extra_interest_first_30k
                self.record_inflow(account='ra', amount=extra_interest_first_30k, message='extra_first30k_interest')
            if combined_balance >= 60_000:
                extra_interest_next_30k = (combined_balance - 30_000) * EXTRA_INTEREST_NEXT_30K_ABOVE_55 / 100
                #self.ra_balance += extra_interest_next_30k
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
# Updated generate_cpf_projection function
def generate_cpf_projection():
    start_date = datetime(2025, 4, 1)
    current_date = start_date

    cpf = CPFAccount()
    cpf.oa_balance = 167892.11
    cpf.sa_balance = 253163.35
    cpf.ma_balance = 72952.37
    cpf.ra_balance = 0.00
    cpf.excess_balance = 0.00
    cpf.loan_balance = 251101.00
    cpf.basic_retirement_sum = BASIC_RETIREMENT_SUM['amount']
    cpf.inflow = {
        'oa_balance': 0.0,
        'sa_balance': 0.0,
        'ma_balance': 0.0,
        'ra_balance': 0.0,
        'loan_balance': 0.0,
        'excess_balance': 0.0
    }
    cpf.ouflow = {
        'oa_balance': 0.0,
        'sa_balance': 0.0,
        'ma_balance': 0.0,
        'ra_balance': 0.0,
        'loan_balance': 0.0,
        'excess_balance': 0.0
    }
    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    retirement_to_transfer = False
    records = []

    for month in range(1, 300):
        # Retrieve age and current date from DATE_DICT
        date_key = cpf.current_date.strftime("%b-%Y")
        age = cpf.get_age(current_date=cpf.current_date)

        if date_key == 'Jul-2029':
            retirement_to_transfer = True

        # Calculate loans
        if cpf.current_date.year <= 2029 and cpf.current_date.month < 7:
            if month < 24:
                loan_payment = LOAN_PAYMENT_YEAR_1_2
            elif 24 <= month < 36:
                loan_payment = LOAN_PAYMENT_YEAR_3
            else:
                loan_payment = LOAN_PAYMENT_YEAR_4_BEYOND

            loan_payment = min(loan_payment, cpf.loan_balance[0])
            cpf.loan_balance = (calculate_loan_balance(cpf.loan_balance[0], interest_rate=2.5, monthly_payment=loan_payment, months=1), "loan_payment")
            
            

        # CPF allocation logic
        if age < AGE_FOR_BRS_TRANSFER['age']:
            for account in ['oa', 'ma', 'sa']:
                allocation = cpf.calculate_cpf_allocation(age=age, salary=SALARY, account=account)
                cpf.record_inflow(account=account, amount=allocation, message='allocation below 55')
        elif age >= AGE_FOR_BRS_TRANSFER['age']:
            for account in ['oa', 'ma', 'ra']:
                allocation = cpf.calculate_cpf_allocation(age=age, salary=SALARY, account=account)
                cpf.record_inflow(account=account, amount=allocation,message='allocation above 55')

        # Module to transfer funds on July 2029
        if retirement_to_transfer:
            cpf.transfer_funds(from_account='sa', to_account='oa', amount=0, is_total_amount=True)
            cpf.transfer_funds(from_account='oa', to_account='ra', amount=BASIC_RETIREMENT_SUM['amount'], is_total_amount=False)
            cpf.record_outflow(account='loan', amount=cpf.loan_balance[0], message='loan_full_payment')
            cpf.record_inflow(account='oa', amount=-cpf.loan_balance[0], message='loan_full_payment')
            cpf.transfer_funds(from_account='oa', to_account='excess', amount=0, is_total_amount=True, message='transfer excess')
            retirement_to_transfer = False

        # Apply interest at the end of the year
        if cpf.current_date.month == 12:
            cpf.apply_interest(age=age)

        # Calculate CPF payout
        cpf_payout = cpf.calculate_cpf_payout(age=age)
        cpf.record_inflow(account='excess', amount=cpf_payout, message=f'cpf_payout {age}')

        # Display balances
        sa_display = f"{cpf.sa_balance[0]:,.2f}" if cpf.sa_balance[0] > 0 else "closed"
        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{sa_display:<15}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{cpf_payout:<12,.2f}")

        # Prepare record for JSON
        record = {
            "date": cpf.custom_serializer(cpf.current_date),
            "age": str(DATE_DICT[date_key]['age']),
            "basic_retirement_sum": cpf.basic_retirement_sum,
            "oa_balance": cpf.oa_balance,
            "oa_log": cpf._oa_log.copy(),
            "sa_balance": cpf.sa_balance,
            "sa_log": cpf._sa_log.copy(),
            "ma_balance": cpf.ma_balance,
            "ma_log": cpf._ma_log.copy(),
            "ra_balance": cpf.ra_balance,
            "ra_log": cpf._ra_log.copy(),
            "loan_balance": cpf.loan_balance,
            "loan_balance_log": cpf._loan_balance_log.copy(),
            "excess_balance": cpf.excess_balance,
            "excess_balance_log": cpf._excess_balance_log.copy(),
        }
        records.append(record)

        # Move to the next month
        cpf.current_date += timedelta(days=30)

    # Save records to a JSON file
    with open("cpf_projection.json", "w") as json_file:
        json.dump(records, json_file, indent=4,default=cpf.custom_serializer)

    print("Projection saved to cpf_projection.json")


def calculate_loan_balance(principal: float, interest_rate: float, monthly_payment: float, months: int) -> float:
    for _ in range(months):
        interest = principal * (interest_rate / 12 / 100)
        principal = principal + interest - monthly_payment
        if principal <= 0:
            return 0.0
    return principal


if __name__ == "__main__":
    generate_cpf_projection()