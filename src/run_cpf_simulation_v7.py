from multiprocessing import Process, Queue
from cpf_config_loader_v3 import ConfigLoader
from cpf_program_v9 import CPFAccount
from cpf_reconfigure_date_v2 import MyDateTime
from tqdm import tqdm  # For the progress bar
from pprint import pprint  # For pretty-printing the dictionary
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from cpf_date_generator_v3 import DateGenerator
import os
import json


## interest to return as amount not computed in class

def loan_computation_first_three_years(cpf, age, date_key, date_info, config_loader):
    loan_payments = config_loader.get('loan_payments', {})
    payment_key = 'year_1_2' if age < 24 else 'year_3'
    loan_payment_amount = float(loan_payments.get(payment_key, 0.0))

def main():
    # Step 1: Load the configuration
    oa_bal = 0.0
    sa_bal = 0.0
    ma_bal = 0.0
    ra_bal = 0.0
    excess_bal = 0.0
    loan_bal = 0.0
    config_loader = ConfigLoader('cpf_config.json')
    start_date = config_loader.get('start_date', {})
    end_date = config_loader.get('end_date', {})
    birth_date = config_loader.get('birth_date', {})
    brs_amount = config_loader.get(['retirement_sums','brs','amount'], {})    
    salary = config_loader.get('salary', {})
    #config_loader.retirement_sums = config_loader.get('retirement_sums', {})

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
    is_display_special_july = False
    # Step 4: Calculate CPF per month using CPFAccount
    with CPFAccount(config_loader) as cpf:
        print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
        print("-" * 150)


        if is_initial:
            print("Loading initial balances from config...")
            # Use property setters to ensure logging
            cpf.date_key = cpf.custom_serializer(cpf.current_date)
            initoa_balance = float(config_loader.get('oa_balance', 0.0))
            initsa_balance = float(config_loader.get('sa_balance', 0.0))
            initma_balance = float(config_loader.get('ma_balance', 0.0))
            initra_balance = float(config_loader.get('ra_balance', 0.0))
            initexcess_balance = float(config_loader.get('excess_balance', 0.0))
            initloan_balance = float(config_loader.get('loan_balance', 0.0))
            #record the updates
            for account, new_balance in zip(['oa', 'sa', 'ma', 'ra', 'excess', 'loan'], [initoa_balance, initsa_balance, initma_balance, initra_balance, initexcess_balance, initloan_balance]):
                cpf.record_inflow(account=account, amount=new_balance, message=f"Initial Balance of {account}")
            is_initial = False
        # Add a blue progress bar for the loop
        for date_key, date_info in tqdm(date_dict.items(), desc="Processing CPF Data", unit="month", colour="blue"):
            age = date_info['age']
            cpf.current_date = date_info['period_end']

            # Determine accounts to process based on age and month
            accounts_to_process = []
            if age <= 55 and cpf.current_date.month <= 7:
                accounts_to_process = ['oa', 'ma', 'sa']
            elif age >= 55 and cpf.current_date.month > 7:
                accounts_to_process = ['oa', 'ma', 'ra']

            # CPF allocation logic
            for account in accounts_to_process:
                cpf.message = f"Processing allocation for {account} at age {age}"
                allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account, config=config_loader)
                cpf.record_inflow(account, allocation, cpf.message)

            # Apply interest at the end of the year
            if cpf.current_date.month == 12:
                
                account_balance = 0.0
                oa_interest = 0.0
                sa_interest = 0.0
                ma_interest = 0.0
                ra_interest = 0.0
                oa_extra_interest = 0.0
                sa_extra_interest = 0.0
                ma_extra_interest = 0.0
                ra_extra_interest = 0.0                

                for account in ['oa', 'sa', 'ma', 'ra']:
                    cpf.message = f"Applying interest for {account} at age {age}"
                    account_balance = getattr(cpf, f'_{account}_balance', 0.0)
                    if account_balance > 0:
                        if account == 'oa':
                            #account: str, age: int, amount: float):
                            oa_interest = cpf.calculate_interest_on_cpf(account=account, age=age, amount=account_balance)
                        elif account == 'sa':
                            sa_interest = cpf.calculate_interest_on_cpf(account=account, age=age, amount=account_balance)
                        elif account == 'ma':
                            ma_interest = cpf.calculate_interest_on_cpf(account=account, age=age, amount=account_balance)
                        elif account == 'ra':
                            ra_interest = cpf.calculate_interest_on_cpf(account=account, age=age, amount=account_balance)
                        # Record the interest inflow                                                       
                oa_extra_interest, sa_extra_interest, ma_extra_interest, ra_extra_interest = cpf.calculate_extra_interest(age=age)
                cpf.record_inflow(account='oa', amount=oa_interest, message=f"Interest for {account} at age {age}")
                cpf.record_inflow(account='sa', amount=sa_interest, message=f"Interest for {account} at age {age}")
                cpf.record_inflow(account='ma', amount=ma_interest, message=f"Interest for {account} at age {age}")
                cpf.record_inflow(account='ra', amount=ra_interest, message=f"Interest for {account} at age {age}")
                cpf.record_inflow(account='oa', amount=oa_extra_interest, message=f"Extra Interest for {account} at age {age}")
                cpf.record_inflow(account='sa', amount=sa_extra_interest, message=f"Extra Interest for {account} at age {age}")
                cpf.record_inflow(account='ma', amount=ma_extra_interest, message=f"Extra Interest for {account} at age {age}")
                cpf.record_inflow(account='ra', amount=ra_extra_interest, message=f"Extra Interest for {account} at age {age}")                                                                                                

            # CPF payout calculation
            cpf_payout = 0.0
            if hasattr(cpf, 'calculate_cpf_payout'):
                payout_result = cpf.calculate_cpf_payout(age=age)
                if isinstance(payout_result, (int, float)):
                    cpf_payout = payout_result
                    cpf.record_inflow('excess', cpf_payout, f"cpf_payout_{age}")

            # Loan payment logic
            if age <= 55:
                loan_payments = config_loader.get('loan_payments', {})
                payment_key = 'year_1_2' if age < 24 else 'year_3'
                loan_payment_amount = float(loan_payments.get(payment_key, 0.0))

                current_loan_balance = getattr(cpf, '_loan_balance', 0.0)
                actual_payment = min(loan_payment_amount, current_loan_balance)
                if actual_payment > 0:
                    cpf.record_outflow('loan', actual_payment, f"loan_payment_{payment_key}")

            # Display balances including July 2029
            cpf.date_key = date_key
            oa_bal = getattr(cpf, '_oa_balance', 0.0).__round__(2)
            sa_bal = getattr(cpf, '_sa_balance', 0.0).__round__(2)
            ma_bal = getattr(cpf, '_ma_balance', 0.0).__round__(2)
            ra_bal = getattr(cpf, '_ra_balance', 0.0).__round__(2)
            loan_bal = getattr(cpf, '_loan_balance', 0.0).__round__(2)
            excess_bal = getattr(cpf, '_excess_balance', 0.0).__round__(2)
           # display_ra = f"{'closed':<15}" if cpf._sa_balance == 0.0 else f'{float(sa_bal):<15,.2f}'
            print(f"{date_key:<15}{age:<5}"
                  f"{float(oa_bal):<15,.2f}{float(sa_bal):<15,.2f}"
                  f"{float(ma_bal):<15,.2f}{float(ra_bal):<15,.2f}"
                  f"{float(loan_bal):<12,.2f}{float(excess_bal):<12,.2f}"
                  f"{float(cpf_payout):<12,.2f}")
            if age == 55 and cpf.current_date.month == 7:
                is_display_special_july = True
                orig_oa_bal = oa_bal
                orig_sa_bal = sa_bal
                orig_ma_bal = ma_bal
                orig_loan_bal = loan_bal
                orig_ra_bal = ra_bal
                orig_excess_bal = excess_bal
            
                                      
            if is_display_special_july:    
                # Special printing for age 55 and month 7
                display_date_key = f"{date_key}-cpf"
                display_oa_bal = -orig_oa_bal
                display_sa_bal = -orig_sa_bal
                display_ma_bal = orig_ma_bal
                display_loan_bal = -orig_loan_bal               
                display_ra_bal =  (orig_oa_bal + orig_sa_bal - orig_loan_bal)
                display_excess_bal = (orig_oa_bal + orig_sa_bal - orig_loan_bal - brs_amount)
                display_cpf_payout = 0.0
                ##                                   
                print(f"{display_date_key:<15}{age:<4}"
                      f"{float(display_oa_bal):<15,.2f}{display_sa_bal:<15,.2f}"
                      f"={float(display_ma_bal):<14,.2f}+{float(display_ra_bal):<14,.2f}"
                      f"{float(display_loan_bal):<13,.2f}{float(display_excess_bal):<12,.2f}"
                      f"{float(display_cpf_payout):<12,.2f}")

                cpf.record_inflow(account= 'oa',  amount= display_oa_bal,  message= f"transfer_cpf_age={age}")
                cpf.record_inflow(account= 'sa',  amount= display_sa_bal,  message= f"transfer_cpf_age={age}")
                cpf.record_inflow(account= 'loan',amount= display_loan_bal,message= f"transfer_cpf_age={age}")
                cpf.record_inflow(account= 'ra',  amount= display_ra_bal,  message= f"transfer_cpf_age={age}")
                cpf.record_inflow(account= 'excess',amount= display_excess_bal,message= f"transfer_cpf_age={age}")
                is_display_special_july = False   
                                                       

if __name__ == "__main__":
    main()

