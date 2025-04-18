from cpf_config_loader_v2 import ConfigLoader
from cpf_date_generator_v2 import generate_date_dict
from cpf_date_utility_v2 import run_simulation
from cpf_program_v6 import CPFAccount
from datetime import datetime, timedelta
from pprint import pprint


def flatten_cpf_summary_as_dict(cpf):
    """
    Flatten the CPF account summary into a dictionary.
    """
    return {
        'current_date': cpf.current_date.strftime('%Y-%m-%d'),
        'oa_balance': cpf.oa_balance[0],
        'sa_balance': cpf.sa_balance[0],
        'ma_balance': cpf.ma_balance[0],
        'ra_balance': cpf.ra_balance[0],
        'excess_balance': cpf.excess_balance[0],
        'loan_balance': cpf.loan_balance[0],
        'basic_retirement_sum': cpf.basic_retirement_sum,
        'full_retirement_sum': cpf.full_retirement_sum,
        'enhanced_retirement_sum': cpf.enhanced_retirement_sum,
        '_oa_log': getattr(cpf, '_oa_log', []),
        '_sa_log': getattr(cpf, '_sa_log', []),
        '_ra_log': getattr(cpf, '_ra_log', []),
        '_excess_log': getattr(cpf, '_excess_log', []),
        '_loan_log': getattr(cpf, '_loan_log', []),
        '_oa_message': cpf._oa_message,
        '_sa_message': cpf._sa_message,
        '_ra_message': cpf._ra_message,
        '_excess_message': cpf._excess_message,
        '_loan_message': cpf._loan_message
        }
    
    
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
    date_dict = generate_date_dict(start_date=start_date, end_date=end_date, birth_date=birth_date)

    # Step 3: Validate dates using cpf_date_utility_v2.py
    valid_dates = run_simulation(config_path='new_config.json', output_format='json')

    # Step 4: Calculate CPF per month using cpf_program_v5.py
    cpf = CPFAccount(config_loader)  # Pass config_loader to CPFAccount

    # Assign balances with default values
  
    cpf.update_balance('oa', config_loader.get('oa_balance', 0), 'initial_oa_balance')
    cpf.update_balance('sa', config_loader.get('sa_balance', 0), 'initial_sa_balance')  
    cpf.update_balance('ma', config_loader.get('ma_balance', 0), 'initial_ma_balance')
    cpf.update_balance('ra', config_loader.get('ra_balance', 0), 'initial_ra_balance')
    cpf.update_balance('excess', config_loader.get('excess_balance', 0), 'initial_excess_balance')
    cpf.update_balance('loan', config_loader.get('loan_balance', 0), 'initial_loan_balance')

    cpf.basic_retirement_sum = config_loader.get('retirement_sums', {}).get('brs', {}).get('amount', 0)
    cpf.full_retirement_sum = config_loader.get('retirement_sums', {}).get('frs', {}).get('amount', 0)
    cpf.enhanced_retirement_sum = config_loader.get('retirement_sums', {}).get('ers', {}).get('amount', 0)

    print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
    print("-" * 150)

    for date_key, date_info in date_dict.items():
        age = date_info['age']
        cpf.current_date = date_info['period_end']
      

        # CPF allocation logic
        for account in ['oa', 'ma', 'sa'] if age < 55 else ['oa', 'ma', 'ra']:
            allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account, config=config_loader)
            cpf.update_balance(account, allocation, f'allocation_{account}')
          #  cpf.record_inflow(account=account, amount=allocation, message=f'allocation_{account}')
        # Apply interest at the end of the year
        if cpf.current_date.month == 12:
            cpf.apply_interest(age=age)
        # CPF payout
        cpf_payout = cpf.calculate_cpf_payout(age=age)
        #cpf.record_inflow(account='excess', amount=cpf_payout, message=f'cpf_payout_{age}')
        cpf.update_balance('excess', cpf_payout, f'cpf_payout_{age}')

       # Loan payment logic
        if age < 55 :
           loan_payments = config_loader.get('loan_payments', {})
           loan_payment = loan_payments.get('year_1_2', 0) if age < 24 else loan_payments.get('year_3', 0)
           loan_payment = min(loan_payment, cpf.loan_balance[0])
          # cpf.loan_balance = (cpf.loan_balance[0] - loan_payment, "loan_payment")
           cpf.update_balance('loan', -loan_payment, 'loan_payment')

        # CPF Transfer of funds at the age of 55
        if age == 55 and cpf.current_date.month == 7:
            cpf.excess_balance = (cpf.oa_balance[0] + cpf.sa_balance[0], "transfer_to_excess")
            cpf.oa_balance = (0, "transfer_to_excess")
            cpf.sa_balance = (0, "transfer_to_excess")
            cpf._ra_balance += cpf.basic_retirement_sum
            cpf._excess_balance -=  cpf.basic_retirement_sum
            cpf._excess_balance -= cpf.loan_balance[0]
            cpf.loan_balance = (0, "loan_full_payment")
            
           # cpf.transfer_to_ra() # ntransfer to EXCESS_BALANCE not RA
           # cpf.loan_balance = (0, "loan_payment")
           # cpf._sa_balance = 0
           # cpf._sa_message = "SA balance zeroed out after transfer to RA and Excess Balance"
           # cpf.excess_balance = (cpf.oa_balance[0] + cpf.sa_balance[0], "transfer_to_excess")
           # cpf.excess_balance ``                                                

        # Display balances
        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{cpf.sa_balance[0]:<15,.2f}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{cpf_payout:<12,.2f}")
       
       
            
        if( age == 55 and cpf.current_date.month == 7) or (age == 55 and cpf.current_date.month == 8):
            flattened_dict = flatten_cpf_summary_as_dict(cpf)
            pprint(flattened_dict)
          
            
        
if __name__ == "__main__":
    main()