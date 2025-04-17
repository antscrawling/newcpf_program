from datetime import datetime, timedelta
from dataclasses import dataclass

# Configuration Parameters
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
AGE_FOR_BRS_TRANSFER = 55
AGE_FOR_CPF_PAYOUT = 67
CPF_PAYOUT_AMOUNT_BRS= BASIC_RETIREMENT_SUM['payout']
CPF_PAYOUT_AMOUNT_FRS= FULL_RETIREMENT_SUM['payout']
CPF_PAYOUT_AMOUNT_ERS= ENHANCED_RETIREMENT_SUM['payout']
CPF_PAYMENT_AMOUNT = BASIC_RETIREMENT_SUM['payout']

SALARY_CAP = 7400
SALARY_ALLOCATION_BELOW_55 = {"oa": 0.23, "sa": 0.06, "ma": 0.08}
SALARY_ALLOCATION_ABOVE_55 = {"oa": 0.115, "ra": 0.105, "ma": 0.075}
SALARY = 9200
LOAN_PAYMENT_YEAR_1_2 = 1687.39
LOAN_PAYMENT_YEAR_3 = 1782.27
LOAN_PAYMENT_YEAR_4_BEYOND = 1817.49
CPF_CONTRIBUTION_RATES= {
    "below_55": {"employee": 0.20, "employer": 0.17},
     "55_to_60": {"employee": 0.15, "employer": 0.14},
     "60_to_65": {"employee": 0.09, "employer": 0.10},
     "65_to_70": {"employee": 0.075, "employer": 0.085},
     "above_70": {"employee": 0.05, "employer": 0.075}
            }

# Updated CPFAccount class with parameterized logic
@dataclass
class CPFAccount:
    current_date: datetime
    oa_balance: float
    sa_balance: float
    ma_balance: float
    basic_retirement_sum: float
    loan_amount: float
    ra_balance: float
    excess_cash: float

    def get_cpf_contribution_rate(self, age):
        if age < 55:
            employee_rate = CPF_CONTRIBUTION_RATES["below_55"]["employee"]
            employer_rate = CPF_CONTRIBUTION_RATES["below_55"]["employer"]
        elif 55 <= age < 60:
            employee_rate = CPF_CONTRIBUTION_RATES["55_to_60"]["employee"]
            employer_rate = CPF_CONTRIBUTION_RATES["55_to_60"]["employer"]
        elif 60 <= age < 65:
            employee_rate = CPF_CONTRIBUTION_RATES["60_to_65"]["employee"]
            employer_rate = CPF_CONTRIBUTION_RATES["60_to_65"]["employer"]
        elif 65 <= age < 70:
            employee_rate = CPF_CONTRIBUTION_RATES["65_to_70"]["employee"]
            employer_rate = CPF_CONTRIBUTION_RATES["65_to_70"]["employer"]
        else:
            employee_rate = CPF_CONTRIBUTION_RATES["above_70"]["employee"]
            employer_rate = CPF_CONTRIBUTION_RATES["above_70"]["employer"]

        return employee_rate, employer_rate
    
    def calculate_cpf_contribution(self,account, salary, age):
        capped_salary = min(salary, SALARY_CAP)
        employee_rate, employer_rate = self.get_cpf_contribution_rate(age)
        employee_contribution = capped_salary * employee_rate
        employer_contribution = capped_salary * employer_rate
        total_contribution = employee_contribution + employer_contribution
       

        if age < AGE_FOR_BRS_TRANSFER:
            self.oa_balance += total_contribution * SALARY_ALLOCATION_BELOW_55["oa"] if account == "oa" else 0
            self.sa_balance += total_contribution * SALARY_ALLOCATION_BELOW_55["sa"]  if account == "sa" else 0 
            self.ma_balance += total_contribution * SALARY_ALLOCATION_BELOW_55["ma"] if account == "ma" else 0
        else:
            self.oa_balance += total_contribution * SALARY_ALLOCATION_ABOVE_55["oa"] if account == "oa" else 0
            self.ra_balance += total_contribution * SALARY_ALLOCATION_ABOVE_55["ra"] if account == "ra" else 0
            self.ma_balance += total_contribution * SALARY_ALLOCATION_ABOVE_55["ma"] if account == "ma" else 0

       # return employee_contribution, employer_contribution    
        
    def apply_interest(self, age):
        oa_interest_rate = OA_INTEREST_RATE_BELOW_55 if age < AGE_FOR_BRS_TRANSFER else OA_INTEREST_RATE_ABOVE_55
        self.oa_balance += self.oa_balance * oa_interest_rate / 100
        self.sa_balance += self.sa_balance * SA_INTEREST_RATE / 100
        self.ma_balance += self.ma_balance * MA_INTEREST_RATE / 100
        self.ra_balance += self.ra_balance * RA_INTEREST_RATE / 100

        self.apply_extra_interest(age)

    def apply_extra_interest(self, age):
        if age < AGE_FOR_BRS_TRANSFER:
            combined_balance = min(self.oa_balance, 20_000) + self.sa_balance + self.ma_balance
            if combined_balance >= 60_000:
                extra_interest = combined_balance * EXTRA_INTEREST_BELOW_55 / 100
            else:
                extra_interest = 0
            self.oa_balance += extra_interest
        else:
            combined_balance = min(self.oa_balance, 20_000) + self.sa_balance + self.ma_balance + self.ra_balance
            if combined_balance >= 30_000:
                first_30k = min(combined_balance, 30_000)
                extra_interest_first_30k = first_30k * EXTRA_INTEREST_FIRST_30K_ABOVE_55 / 100
                self.ra_balance += extra_interest_first_30k
            if combined_balance >= 60_000:
                extra_interest_next_30k = (combined_balance - 30_000) * EXTRA_INTEREST_NEXT_30K_ABOVE_55 / 100
                self.ra_balance += extra_interest_next_30k

    def calculate_excess_cash(self):
        return (self.oa_balance + self.sa_balance) - self.ra_balance - self.loan_amount

    def calculate_cpf_payout(self, age):
        return CPF_PAYOUT_AMOUNT_BRS if age >= AGE_FOR_CPF_PAYOUT else 0

    def calculate_sa_balance(self, amount):
        self.sa_balance += amount

    def calculate_oa_balance(self, amount):
        self.oa_balance += amount

    def calculate_ma_balance(self, amount):
        self.ma_balance += amount

    def calculate_ra_balance(self, amount):
        self.ra_balance += amount

# Updated generate_cpf_projection function
def generate_cpf_projection():
    start_date = datetime(2025, 4, 1)
    birth_date = datetime(1974, 7, 6)
    current_date = start_date

    oa_balance = 167892.11
    sa_balance = 253163.35
    ma_balance = 72952.37
    ra_balance = 0.00
    excess_cash = 0.00
    loan_amount = 251101.00

    cpf = CPFAccount(current_date, oa_balance, sa_balance, ma_balance, BASIC_RETIREMENT_SUM, loan_amount, ra_balance, excess_cash)
    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    bsr_transferred = False

    for month in range(1,300):
        age = cpf.current_date.year - birth_date.year - (
            (cpf.current_date.month, cpf.current_date.day) < (birth_date.month, birth_date.day)
        )

        if current_date.year <= 2029 and current_date.month < 7:
            if month < 24:
                loan_payment = LOAN_PAYMENT_YEAR_1_2
            elif 24 <= month < 36:
                loan_payment = LOAN_PAYMENT_YEAR_3
            else:
                loan_payment = LOAN_PAYMENT_YEAR_4_BEYOND

            loan_payment = min(loan_payment, cpf.loan_amount)
            cpf.loan_amount -= loan_payment
            cpf.loan_amount = max(cpf.loan_amount, 0)

     

    
        cpf.calculate_cpf_contribution('oa',SALARY, age)
        cpf.calculate_cpf_contribution('ma',SALARY, age)
    
        if age == AGE_FOR_BRS_TRANSFER and cpf.current_date.month == 7 and cpf.current_date.year == 2029:
            
            cpf.calculate_cpf_contribution('sa',SALARY, age)
        
            cpf.calculate_ra_balance(BASIC_RETIREMENT_SUM['amount'])
            cpf.calculate_oa_balance(-BASIC_RETIREMENT_SUM['amount'])

            cpf.excess_cash += cpf.oa_balance + cpf.sa_balance
            cpf.oa_balance = 0
            cpf.sa_balance = 0
            cpf.loan_amount = 0
            bsr_transferred = True
        elif age > AGE_FOR_BRS_TRANSFER and cpf.current_date > datetime(2029, 7, 31) :     
            cpf.calculate_cpf_contribution('ra', SALARY, age)          
        elif age <AGE_FOR_BRS_TRANSFER :  
            cpf.calculate_cpf_contribution('sa', SALARY, age)
      
            

      

        if current_date.month == 12:
            cpf.apply_interest(age)

        cpf_payout = cpf.calculate_cpf_payout(age)
        cpf.excess_cash += cpf_payout

        sa_display = f"{cpf.sa_balance:,.2f}" if cpf.sa_balance > 0 else "closed"

        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance:<15,.2f}{sa_display:<15}{cpf.ma_balance:<15,.2f}{cpf.ra_balance:<15,.2f}{cpf.loan_amount:<12,.2f}{cpf.excess_cash:<12,.2f}{cpf_payout:<12,.2f}")

        cpf.current_date += timedelta(days=30)
        current_date = cpf.current_date

if __name__ == "__main__":
    generate_cpf_projection()