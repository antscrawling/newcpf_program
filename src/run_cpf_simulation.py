from cpf_config_loader_v2 import ConfigLoader
from cpf_date_generator_v2 import generate_date_dict
from cpf_date_utility_v2 import run_simulation
from cpf_program_v5 import CPFAccount
from datetime import datetime, timedelta

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

def transfer_to_ra(self):
    """Transfer OA and SA balances to RA at age 55, up to the Basic Retirement Sum (BRS).
    The remaining amount is transferred to the Excess Balance."""
    # Step 1: Pay the Loan Balance in Full
    total_funds = self._oa_balance + self._sa_balance
    loan_payment = min(total_funds, self._loan_balance)
    self.record_outflow('oa', min(self._oa_balance, loan_payment), 'loan_fully_paid')
    loan_payment -= min(self._oa_balance, loan_payment)
    self.record_outflow('sa', loan_payment, 'loan_fully_paid')
    self._loan_balance = 0

    # Step 2: Transfer Remaining OA + SA to Excess Balance
    remaining_funds = self._oa_balance + self._sa_balance
    self.record_outflow('oa', self._oa_balance, 'transfer_to_excess')
    self.record_outflow('sa', self._sa_balance, 'transfer_to_excess')
    self.record_inflow('excess', remaining_funds, 'transfer_to_excess')

    # Step 3: Transfer BRS to RA
    brs = self.basic_retirement_sum
    transfer_to_ra = min(remaining_funds, brs)
    self.record_outflow('excess', transfer_to_ra, 'transfer_to_ra')
    self.record_inflow('ra', transfer_to_ra, 'transfer_to_ra')

    # Step 4: Zero Out SA Balance
    self._sa_balance = 0
    self._sa_message = "SA balance zeroed out after transfer to RA and Excess Balance"

def transfer_to_excess(self):
    """Transfer OA and SA balances to Excess Balance, pay the loan in full, and close SA balance."""
    # Step 1: Transfer OA + SA to Excess Balance
    total_transfer = self._oa_balance + self._sa_balance
    self.record_outflow('oa', self._oa_balance, 'transfer_to_excess')
    self.record_outflow('sa', self._sa_balance, 'transfer_to_excess')
    self.record_inflow('excess', total_transfer, 'transfer_to_excess')

    # Step 2: Pay the Loan Balance in Full
    loan_payment = min(total_transfer, self._loan_balance)
    self.record_outflow('excess', loan_payment, 'loan_fully_paid')
    self._loan_balance -= loan_payment

    # Step 3: Zero Out SA Balance
    self._sa_balance = 0
    self._sa_message = "SA balance zeroed out after transfer to Excess Balance"

    # Step 4: Mark SA Balance as Closed
    self._sa_closed = True  # Add a flag to indicate the SA balance is closed
    self._sa_message = "SA officially closed after transfer to Excess Balance"

def generate_cpf_projection():
    config_loader = ConfigLoader('cpf_config.json')
    cpf = CPFAccount(config_loader)
    cpf.current_date = datetime.strptime(config_loader.get('start_date'), "%Y-%m-%d")

    cpf.oa_balance = config_loader.get('oa_balance', 0)
    cpf.sa_balance = config_loader.get('sa_balance', 0)
    cpf.ma_balance = config_loader.get('ma_balance', 0)
    cpf.ra_balance = config_loader.get('ra_balance', 0)
    cpf.excess_balance = config_loader.get('excess_balance', 0)
    cpf.loan_balance = config_loader.get('loan_balance', 0)

    cpf.basic_retirement_sum = config_loader.get('retirement_sums', {}).get('brs', {}).get('amount', 0)
    cpf.full_retirement_sum = config_loader.get('retirement_sums', {}).get('frs', {}).get('amount', 0)
    cpf.enhanced_retirement_sum = config_loader.get('retirement_sums', {}).get('ers', {}).get('amount', 0)

    salary = config_loader.get('salary', 0)
    
    # Track if SA is closed
    sa_closed = False

    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    for month in range(1, 300):
        age = cpf.get_age(current_date=cpf.current_date)
        current_month_year = cpf.current_date.strftime('%b-%Y')

        # Special handling for July 2029 (age 55) - ONE TIME TRANSFER
        if age == 55 and current_month_year == 'Jul-2029':
            # Step 1: Transfer OA and SA to Excess Balance
            total_transfer = cpf.oa_balance[0] + cpf.sa_balance[0]
            cpf.record_outflow('oa', cpf.oa_balance[0], 'transfer_to_excess')
            cpf.record_outflow('sa', cpf.sa_balance[0], 'transfer_to_excess')
            cpf.record_inflow('excess', total_transfer, 'transfer_to_excess')
            
            # Step 2: Pay loan in full from Excess Balance
            loan_payment = min(cpf.excess_balance[0], cpf.loan_balance[0])
            cpf.record_outflow('excess', loan_payment, 'loan_fully_paid')
            cpf.loan_balance = (cpf.loan_balance[0] - loan_payment, "loan_fully_paid")
            
            # Step 3: Close SA Account
            sa_closed = True
            cpf.sa_balance = (0, "SA closed after transfer to Excess Balance")
            
        # Skip operations on SA if it is closed
        if sa_closed:
            cpf.sa_balance = (0, "SA account is closed")

        # CPF allocation logic - Skip SA if closed
        for account in ['oa', 'ma', 'sa'] if age < 55 and not sa_closed else ['oa', 'ma', 'ra']:
            if account == 'sa' and sa_closed:
                continue
            allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account, config=config_loader)
            cpf.record_inflow(account=account, amount=allocation, message=f'allocation_{account}')

        # BRS payouts at age 67+
        if age >= 67:
            brs_payout = config_loader.get('retirement_sums', {}).get('brs', {}).get('payout', 0)
            cpf.record_inflow('excess', brs_payout, f'brs_payout_{age}')

        # Apply interest at the end of the year
        if cpf.current_date.month == 12:
            # Skip SA interest if closed
            for account in ['oa', 'ma', 'ra', 'sa']:
                if account == 'sa' and sa_closed:
                    continue
                interest_rate = config_loader.get('interest_rates', {}).get(account, 2.5)
                balance = getattr(cpf, f'_{account}_balance')
                if balance > 0:
                    cpf.record_inflow(account, balance * (interest_rate / 100 / 12), 'interest')

        # Ensure SA balance stays at 0 if closed
        if sa_closed:
            cpf._sa_balance = 0
            cpf._sa_message = "SA account is closed"

        # Display balances
        print(f"{current_month_year:<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{cpf.sa_balance[0]:<15,.2f}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{0.0:<12,.2f}")

        # Move to the next month
        cpf.current_date += timedelta(days=30)

def main():
    # Step 1: Load the configuration
    config_loader = ConfigLoader('new_config.json')
    start_date = config_loader.get('start_date', 0)
    end_date = config_loader.get('end_date', 0)
    birth_date = config_loader.get('birth_date', 0)
    salary = config_loader.get('salary', 0)

    # Validate that the dates are loaded correctly
    if not all([start_date, end_date, birth_date]):
        raise ValueError("Missing required date values in the configuration file. Please check 'start_date', 'end_date', and 'birth_date'.")

    # Step 2: Generate the date dictionary
    date_dict = generate_date_dict(start_date=start_date, end_date=end_date, birth_date=birth_date)

    # Step 3: Validate dates using cpf_date_utility_v2.py
    valid_dates = run_simulation(config_path='new_config.json', output_format='json')

    # Step 4: Calculate CPF per month using cpf_program_v5.py
    cpf = CPFAccount(config_loader)  # Pass config_loader to CPFAccount

    # Assign balances with default values
    cpf.oa_balance = config_loader.get('oa_balance', 0)
    cpf.sa_balance = config_loader.get('sa_balance', 0)
    cpf.ma_balance = config_loader.get('ma_balance', 0)
    cpf.ra_balance = config_loader.get('ra_balance', 0)
    cpf.excess_balance = config_loader.get('excess_balance', 0)
    cpf.loan_balance = config_loader.get('loan_balance', 0)

    cpf.basic_retirement_sum = config_loader.get('retirement_sums', {}).get('brs', {}).get('amount', 0)
    cpf.full_retirement_sum = config_loader.get('retirement_sums', {}).get('frs', {}).get('amount', 0)
    cpf.enhanced_retirement_sum = config_loader.get('retirement_sums', {}).get('ers', {}).get('amount', 0)

    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    for date_key, date_info in date_dict.items():
        age = date_info['age']
        cpf.current_date = date_info['period_end']

        # Loan payment logic
        loan_payments = config_loader.get('loan_payments', {})
        loan_payment = loan_payments.get('year_1_2', 0) if age < 24 else loan_payments.get('year_3', 0)
        loan_payment = min(loan_payment, cpf.loan_balance[0])
        cpf.loan_balance = (cpf.loan_balance[0] - loan_payment, "loan_payment")

        # CPF Transfer of funds at the age of 55
        if age == 55:
            cpf.transfer_to_ra()
            cpf.loan_balance = (0, "loan_payment")
            cpf.excess_balance = (cpf.oa_balance[0] + cpf.sa_balance[0], "transfer_to_excess")

        # CPF allocation logic
        for account in ['oa', 'ma', 'sa'] if age < 55 else ['oa', 'ma', 'ra']:
            allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account, config=config_loader)
            cpf.record_inflow(account=account, amount=allocation, message=f'allocation_{account}')

        # Apply interest at the end of the year
        if cpf.current_date.month == 12:
            cpf.apply_interest(age=age)

        # CPF payout
        cpf_payout = cpf.calculate_cpf_payout(age=age)
        cpf.record_inflow(account='excess', amount=cpf_payout, message=f'cpf_payout_{age}')

        # Display balances
        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{cpf.sa_balance[0]:<15,.2f}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{cpf_payout:<12,.2f}")

if __name__ == "__main__":
    main()