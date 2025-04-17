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

BASIC_RETIREMENT_SUM = 106500
AGE_FOR_BRS_TRANSFER = 55
AGE_FOR_CPF_PAYOUT = 67
CPF_PAYOUT_AMOUNT = 730

SALARY_CAP = 7400
SALARY_ALLOCATION_BELOW_55 = {"oa": 0.23, "sa": 0.06, "ma": 0.08}
SALARY_ALLOCATION_ABOVE_55 = {"oa": 0.115, "ra": 0.105, "ma": 0.075}

LOAN_PAYMENT_YEAR_1_2 = 1687.39
LOAN_PAYMENT_YEAR_3 = 1782.27
LOAN_PAYMENT_YEAR_4_BEYOND = 1817.49

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
        return CPF_PAYOUT_AMOUNT if age >= AGE_FOR_CPF_PAYOUT else 0

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

    for month in range(240):
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

        capped_salary = min(SALARY_CAP, 9200)

        if age < AGE_FOR_BRS_TRANSFER:
            cpf.calculate_oa_balance(capped_salary * SALARY_ALLOCATION_BELOW_55["oa"])
            cpf.calculate_sa_balance(capped_salary * SALARY_ALLOCATION_BELOW_55["sa"])
            cpf.calculate_ma_balance(capped_salary * SALARY_ALLOCATION_BELOW_55["ma"])

        elif age == AGE_FOR_BRS_TRANSFER and cpf.current_date.month == birth_date.month and not bsr_transferred:
            cpf.calculate_oa_balance(capped_salary * SALARY_ALLOCATION_BELOW_55["oa"])
            cpf.calculate_sa_balance(capped_salary * SALARY_ALLOCATION_BELOW_55["sa"])
            cpf.calculate_ma_balance(capped_salary * SALARY_ALLOCATION_BELOW_55["ma"])

            cpf.calculate_ra_balance(BASIC_RETIREMENT_SUM)
            cpf.calculate_oa_balance(-BASIC_RETIREMENT_SUM)

            cpf.excess_cash += cpf.oa_balance + cpf.sa_balance
            cpf.oa_balance = 0
            cpf.sa_balance = 0
            cpf.loan_amount = 0
            bsr_transferred = True

        elif age >= AGE_FOR_BRS_TRANSFER and (cpf.current_date.month > birth_date.month or cpf.current_date.year > birth_date.year):
            cpf.calculate_oa_balance(capped_salary * SALARY_ALLOCATION_ABOVE_55["oa"])
            cpf.calculate_ma_balance(capped_salary * SALARY_ALLOCATION_ABOVE_55["ma"])
            cpf.calculate_ra_balance(capped_salary * SALARY_ALLOCATION_ABOVE_55["ra"])

        if current_date.month == 12:
            cpf.apply_interest(age)

        cpf_payout = cpf.calculate_cpf_payout(age)

        sa_display = f"{cpf.sa_balance:,.2f}" if cpf.sa_balance > 0 else "closed"

        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance:<15,.2f}{sa_display:<15}{cpf.ma_balance:<15,.2f}{cpf.ra_balance:<15,.2f}{cpf.loan_amount:<12,.2f}{cpf.excess_cash:<12,.2f}{cpf_payout:<12,.2f}")

        cpf.current_date += timedelta(days=30)
        current_date = cpf.current_date

if __name__ == "__main__":
    generate_cpf_projection()