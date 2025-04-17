from datetime import datetime, timedelta
from dataclasses import dataclass

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
        oa_interest_rate = 2.5 if age < 55 else 4.0
        sa_interest_rate = 4.0
        ma_interest_rate = 4.0
        ra_interest_rate = 4.0

        self.oa_balance += self.oa_balance * oa_interest_rate / 100
        self.sa_balance += self.sa_balance * sa_interest_rate / 100
        self.ma_balance += self.ma_balance * ma_interest_rate / 100
        self.ra_balance += self.ra_balance * ra_interest_rate / 100

        self.apply_extra_interest(age)

    def apply_extra_interest(self, age):
        if age < 55:  # all extra income is added to oa balance
            if (combined_balance := min(self.oa_balance,20_000) + self.sa_balance + self.ma_balance) >=60_000:         
                extra_interest = combined_balance * 1.0 / 100
            else:
                extra_interest = 0
            self.oa_balance += extra_interest
            
        else:  # all extra income is added to ra balance
            if (combined_balance := min(self.oa_balance,20_000) + self.sa_balance + self.ma_balance + self.ra_balance) >=30_000:
                first_30k = min(combined_balance, 30000)
                extra_interest_first_30k = first_30k * 2.0 / 100
                self.ra_balance += extra_interest_first_30k
            elif combined_balance >= 60_000:                
                extra_interest_next_30k = (combined_balance -30_000) * 1.0 / 100
                self.ra_balance += extra_interest_next_30k             
                                                   
    def calculate_excess_cash(self):
        return (self.oa_balance + self.sa_balance) - self.ra_balance - self.loan_amount

    def calculate_cpf_payout(self, age):
        return 730 if age >= 67 else 0

    def calculate_sa_balance(self, amount):
        self.sa_balance += amount

    def calculate_oa_balance(self, amount):
        self.oa_balance += amount

    def calculate_ma_balance(self, amount):
        self.ma_balance += amount

    def calculate_ra_balance(self, amount):
        self.ra_balance += amount

def generate_cpf_projection():
    start_date = datetime(2025, 4, 1)
    birth_date = datetime(1974, 7, 6)
    current_date = start_date

    basic_retirement_sum = 106500
    loan_amount = 251101.00
    salary = 9200
    salary_cap = 7400

    oa_balance = 167892.11
    sa_balance = 253163.35
    ma_balance = 72952.37
    ra_balance = 0.00
    excess_cash = 0.00

    loan_payment_year_1_2 = 1687.39
    loan_payment_year_3 = 1782.27
    loan_payment_year_4_beyond = 1817.49

    cpf = CPFAccount(current_date, oa_balance, sa_balance, ma_balance, basic_retirement_sum, loan_amount, ra_balance, excess_cash)
    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    bsr_transferred = False

    for month in range(240):
        age = cpf.current_date.year - birth_date.year - (
            (cpf.current_date.month, cpf.current_date.day) < (birth_date.month, birth_date.day)
        )

        if current_date.year <= 2029 and current_date.month < 7:
            if month < 24:
                loan_payment = loan_payment_year_1_2
            elif 24 <= month < 36:
                loan_payment = loan_payment_year_3
            else:
                loan_payment = loan_payment_year_4_beyond

            loan_payment = min(loan_payment, cpf.loan_amount)
            cpf.loan_amount -= loan_payment
            cpf.loan_amount = max(cpf.loan_amount, 0)

        capped_salary = min(salary, salary_cap)

        if age < 55:
            cpf.calculate_oa_balance(capped_salary * 0.23)
            cpf.calculate_sa_balance(capped_salary * 0.06)
            cpf.calculate_ma_balance(capped_salary * 0.08)

        elif age == 55 and cpf.current_date.month == birth_date.month and not bsr_transferred:
            cpf.calculate_oa_balance(capped_salary * 0.23)
            cpf.calculate_sa_balance(capped_salary * 0.06)
            cpf.calculate_ma_balance(capped_salary * 0.08)

            cpf.calculate_ra_balance(cpf.basic_retirement_sum)
            cpf.calculate_oa_balance(-cpf.basic_retirement_sum)

            cpf.excess_cash += cpf.oa_balance + cpf.sa_balance
            cpf.oa_balance = 0
            cpf.sa_balance = 0
            cpf.loan_amount = 0
            bsr_transferred = True

        elif age >= 55 and (cpf.current_date.month > birth_date.month or cpf.current_date.year > birth_date.year):
            cpf.calculate_oa_balance(capped_salary * 0.115)
            cpf.calculate_ma_balance(capped_salary * 0.075)
            cpf.calculate_ra_balance(capped_salary * 0.105)

        if current_date.month == 12:
            cpf.apply_interest(age)

        cpf_payout = cpf.calculate_cpf_payout(age)

        sa_display = f"{cpf.sa_balance:,.2f}" if cpf.sa_balance > 0 else "closed"

        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance:<15,.2f}{sa_display:<15}{cpf.ma_balance:<15,.2f}{cpf.ra_balance:<15,.2f}{cpf.loan_amount:<12,.2f}{cpf.excess_cash:<12,.2f}{cpf_payout:<12,.2f}")

        cpf.current_date += timedelta(days=30)
        current_date = cpf.current_date

if __name__ == "__main__":
    generate_cpf_projection()

