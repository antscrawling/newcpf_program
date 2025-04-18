from multiprocessing import Process, Queue
from cpf_config_loader_v2 import ConfigLoader
from cpf_program_v6 import CPFAccount
from tqdm import tqdm  # For the progress bar


def main():
    # Step 1: Load the configuration
    config_loader = ConfigLoader('new_config.json')
    start_date = config_loader.get('start_date', 0)
    end_date = config_loader.get('end_date', 0)
    birth_date = config_loader.get('birth_date', 0)
    salary = config_loader.get('salary', 0)
    config_loader.retirement_sums = config_loader.get('retirement_sums', {})

    # Validate that the dates are loaded correctly
    if not all([start_date, end_date, birth_date]):
        raise ValueError("Missing required date values in the configuration file. Please check 'start_date', 'end_date', and 'birth_date'.")

    # Step 2: Generate the date dictionary
    date_dict = CPFAccount(config_loader).get_date_dict(start_date=start_date, end_date=end_date, birth_date=birth_date)

    # Step 3: Validate dates using cpf_date_utility_v2.py
    # Assuming run_simulation validates the dates and returns valid ones
    valid_dates = date_dict  # Placeholder for actual validation logic

    # Step 4: Calculate CPF per month using CPFAccount
    with CPFAccount(config_loader) as cpf:  # Use the context manager
        print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
        print("-" * 150)

        # Add a blue progress bar for the loop
        for date_key, date_info in tqdm(date_dict.items(), desc="Processing CPF Data", unit="month", colour="blue"):
            age = date_info['age']
            cpf.current_date = date_info['period_end']

            # CPF allocation logic
            for account in ['oa', 'ma', 'sa'] if age < 55 else ['oa', 'ma', 'ra']:
                allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account, config=config_loader)
                cpf.update_balance(account, allocation, f'allocation_{account}')

            # Apply interest at the end of the year
            if cpf.current_date.month == 12:
                cpf.apply_interest(age=age)

            # CPF payout
            cpf_payout = cpf.calculate_cpf_payout(age=age)
            cpf.update_balance('excess', cpf_payout, f'cpf_payout_{age}')

            # Loan payment logic
            if age < 55:
                loan_payments = config_loader.get('loan_payments', {})
                loan_payment = loan_payments.get('year_1_2', 0) if age < 24 else loan_payments.get('year_3', 0)
                loan_payment = min(loan_payment, cpf.loan_balance[0])
                cpf.update_balance('loan', -loan_payment, 'loan_payment')

            # CPF Transfer of funds at the age of 55
            if age == 55 and cpf.current_date.month == 7:
                cpf.transfer_to_ra()

            # Display balances
            print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{cpf.sa_balance[0]:<15,.2f}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{cpf_payout:<12,.2f}")


if __name__ == "__main__":
    main()

