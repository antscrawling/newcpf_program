from cpf_config_loader_v2 import ConfigLoader
from cpf_date_generator_v2 import generate_date_dict
from cpf_date_utility_v2 import run_simulation
from cpf_program_v5 import CPFAccount

def main():
    # Step 1: Load the configuration
    config_loader = ConfigLoader('new_config.json')
    start_date = config_loader.get('start_date')
    end_date = config_loader.get('end_date')
    birth_date = config_loader.get('birth_date')
    salary = config_loader.get('salary')

    # Validate that the dates are loaded correctly
    if not all([start_date, end_date, birth_date]):
        raise ValueError("Missing required date values in the configuration file. Please check 'start_date', 'end_date', and 'birth_date'.")

    # Step 2: Generate the date dictionary
    date_dict = generate_date_dict(start_date=start_date, end_date=end_date, birth_date=birth_date)

    # Step 3: Validate dates using cpf_date_utility_v2.py
    valid_dates = run_simulation(config_path='new_config.json', output_format='json')

    # Step 4: Calculate CPF per month using cpf_program_v5.py
    cpf = CPFAccount(config_loader.data)
    cpf.oa_balance = config_loader.get('initial_balances')['oa_balance'], 'initial'
    cpf.sa_balance = config_loader.get('initial_balances')['sa_balance'], 'initial'
    cpf.ma_balance = config_loader.get('initial_balances')['ma_balance'], 'initial'
    cpf.ra_balance = config_loader.get('initial_balances')['ra_balance'], 'initial'
    cpf.excess_balance = config_loader.get('initial_balances')['excess_balance'], 'initial'
    cpf.loan_balance = config_loader.get('initial_balances')['loan_balance'], 'initial'
    cpf.basic_retirement_sum = config_loader.get('retirement_sums')['brs']['amount']
    cpf.full_retirement_sum = config_loader.get('retirement_sums')['frs']['amount']
    cpf.enhanced_retirement_sum = config_loader.get('retirement_sums')['ers']['amount']

    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    for date_key, date_info in date_dict.items():
        age = date_info['age']
        cpf.current_date = date_info['period_end']

        # Loan payment logic
        if cpf.current_date.year <= 2029 and cpf.current_date.month < 7:
            loan_payment = config_loader.get('loan_payments')['year_1_2'] if age < 24 else config_loader.get('loan_payments')['year_3']
            loan_payment = min(loan_payment, cpf.loan_balance[0])
            cpf.loan_balance = (cpf.loan_balance[0] - loan_payment, "loan_payment")

        # CPF Transfer of funds at the age of 55. All oa_balance + sa_balance transferred to ra_balance.
        # Pay off the full loan amount, excess cash transferred to excess_balance
        if age == 55:
            cpf.transfer_to_ra()
            cpf.loan_balance = (0, "loan_payment")
            cpf.excess_balance = (cpf.oa_balance[0] + cpf.sa_balance[0], "transfer_to_excess")

        # CPF allocation logic
        for account in ['oa', 'ma', 'sa'] if age < 55 else ['oa', 'ma', 'ra']:
            allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account)
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