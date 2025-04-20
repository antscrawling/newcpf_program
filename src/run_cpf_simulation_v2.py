from multiprocessing import Process, Queue
from cpf_config_loader_v2 import ConfigLoader
from cpf_program_v6 import CPFAccount
from cpf_reconfigure_date_v2 import MyDateTime
from tqdm import tqdm  # For the progress bar
from pprint import pprint  # For pretty-printing the dictionary
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from cpf_date_generator_v3 import DateGenerator
import os
import json


def main():
    # Step 1: Load the configuration

    config_loader = ConfigLoader('new_config.json')
    start_date = config_loader.get('start_date', {})
    end_date = config_loader.get('end_date', {})
    birth_date = config_loader.get('birth_date', {})

    
    
    salary = config_loader.get('salary', {})
    config_loader.retirement_sums = config_loader.get('retirement_sums', {})

    # Validate that the dates are loaded correctly
    if not all([start_date, end_date, birth_date]):
        raise ValueError("Missing required date values in the configuration file. Please check 'start_date', 'end_date', and 'birth_date'.")

    # Step 2: Generate the date dictionary
    dategen = DateGenerator(start_date=start_date, end_date=end_date, birth_date=birth_date)
    date_dict = dategen.generate_date_dict()
    print(f"Generated date_dict with {len(date_dict)} entries.")
    if not date_dict:
        print("Error: date_dict is empty. Loop will not run.")
        return  # Exit if empty

    is_initial = True

    # Step 4: Calculate CPF per month using CPFAccount
    with CPFAccount(config_loader) as cpf:
        print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
        print("-" * 150)


        if is_initial:
            print("Loading initial balances from config...")
            cpf._oa_balance = float(config_loader.get('oa_balance', 0.0))
            cpf._sa_balance = float(config_loader.get('sa_balance', 0.0))
            cpf._ma_balance = float(config_loader.get('ma_balance', 0.0))
            cpf._ra_balance = float(config_loader.get('ra_balance', 0.0))
            cpf._excess_balance = float(config_loader.get('excess_balance', 0.0))
            cpf._loan_balance = float(config_loader.get('loan_balance', 0.0))
            is_initial = False
        # Add a blue progress bar for the loop
        for date_key, date_info in tqdm(date_dict.items(), desc="Processing CPF Data", unit="month", colour="blue"):
            age = date_info['age']
            cpf.current_date = date_info['period_end']
            if not isinstance(cpf.current_date, (date, datetime)):
                raise TypeError(f"Invalid date type for cpf.current_date: {type(cpf.current_date)}")

            # CPF allocation logic
            accounts_to_process = ['oa', 'ma', 'sa'] if age < 55 else ['oa', 'ma', 'ra']
            for account in accounts_to_process:
                allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account, config=config_loader)
                cpf.record_inflow(account, allocation, f'allocation_{account}')

            # Apply interest at the end of the year

            if cpf.current_date.month == 12:
                cpf.apply_interest(age=age)

            # CPF payout calculation
            cpf_payout: float = 0.0
            if hasattr(cpf, 'calculate_cpf_payout'):
                payout_result = cpf.calculate_cpf_payout(age=age)
                if isinstance(payout_result, (int, float)):
                    cpf_payout = payout_result
                    cpf.record_inflow('excess', cpf_payout, f'cpf_payout_{age}')
                else:
                    print(f"Warning: calculate_cpf_payout returned non-numeric value: {payout_result}")
            else:
                print("Warning: CPFAccount missing calculate_cpf_payout method.")

            # Loan payment logic
            if age < 55:
                loan_payments = config_loader.get('loan_payments', {})
                payment_key = 'year_1_2' if age < 24 else 'year_3'
                loan_payment_amount = float(loan_payments.get(payment_key, 0.0))

                current_loan_balance = getattr(cpf, '_loan_balance', 0.0)
                if not isinstance(current_loan_balance, (float, int)):
                    print(f"Warning: Current loan balance is not a number ({current_loan_balance}). Resetting to 0.0.")
                    current_loan_balance = 0.0
                    setattr(cpf, '_loan_balance', 0.0)

                actual_payment = min(loan_payment_amount, current_loan_balance)
                if actual_payment > 0:
                    cpf.record_outflow('loan', actual_payment, f'loan_payment_{payment_key}')

            # CPF Transfer of funds at the age of 55
            if age == 55 and cpf.current_date.month == 7:
                if hasattr(cpf, 'transfer_to_ra'):
                   
                    cpf.transfer_to_ra(age=age, retirement_type='basic')
                else:
                    print("Warning: CPFAccount missing transfer_to_ra method.")

            # Display balances
            oa_bal = getattr(cpf, '_oa_balance', 0.0)
            sa_bal = getattr(cpf, '_sa_balance', 0.0)
            ma_bal = getattr(cpf, '_ma_balance', 0.0)
            ra_bal = getattr(cpf, '_ra_balance', 0.0)
            loan_bal = getattr(cpf, '_loan_balance', 0.0)
            excess_bal = getattr(cpf, '_excess_balance', 0.0)

            print(f"{date_key:<15}{age:<5}"
                  f"{float(oa_bal):<15,.2f}{float(sa_bal):<15,.2f}"
                  f"{float(ma_bal):<15,.2f}{float(ra_bal):<15,.2f}"
                  f"{float(loan_bal):<12,.2f}{float(excess_bal):<12,.2f}"
                  f"{float(cpf_payout):<12,.2f}")
        
            

if __name__ == "__main__":
    main()

