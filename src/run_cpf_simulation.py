from cpf_config_loader_v2 import ConfigLoader
from cpf_date_generator_v2 import generate_date_dict
from cpf_date_utility_v2 import run_simulation
from cpf_program_v6 import CPFAccount
from datetime import datetime, timedelta
from pprint import pprint

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

def xtransfer_to_ra(self):
    """Transfer OA and SA balances to RA at age 55, up to the Basic Retirement Sum (BRS).
    The remaining amount is transferred to the Excess Balance."""
    # Step 1: Pay the Loan Balance in Full
    excess_balance  = self._oa_balance + self._sa_balance
    self.record_outflow('oa', self._oa_balance, 'transfer_to_excess')
    self.record_outflow('sa', self._sa_balance, 'transfer_to_excess')
    self.record_inflow('excess', excess_balance, 'transfer_to_excess')
    self.record_outflow('excess', self._loan_balance, 'loan_fully_paid')
    #self.excess_balance -= self._loan_balance
    self.record_outflow('excess', -self._loan_balance, 'loan_fully_paid')
    #self.ra_balance += 106500
    self.record_inflow('ra', 106500, 'transfer_to_ra')
    self._sa_balance = 0
    self._sa_message = "SA balance zeroed out after transfer to RA and Excess Balance"


def xtransfer_to_ra(self):
    """Transfer OA and SA balances to RA at age 55, up to the Basic Retirement Sum (BRS).
    The remaining amount is transferred to the Excess Balance."""
    # Step 1: Pay the Loan Balance in Full
   # self.excess_balance  = self._oa_balance + self._sa_balance
    self.update_balance('excess', self.oa_balance, 'transfer_oa_to_excess')
    self.update_balance('excess', self.sa_balance, 'transfer_sa_to_excess')
    self.update_balance('excess', self.loan_balance, 'loan_fully_paid')
    self.update_balance('ra', self.basic_retirement_sum, 'transfer_to_ra')
    self.update_balance('loan', -self.loan_balance, 'loan_fully_paid')
    
    


def flatten_cpf_summary_as_dict(cpf):
    result = {"Date": [str(cpf.current_date)]}   
    for section_name, data in [("Inflow", cpf.inflow), ("Outflow", cpf.outflow)]:
        for key, value in data.items():
            col_name = f'|{section_name}|{key}'
            result[col_name] = round(value, 2)
           #if (section_name == "Inflow" and value ==0) or (section_name == "Outflow" and value == 0):
           #    continue
           #else:
           #    result[f'{section_name}-{key}'] = 1*round(value, 2) if section_name == "Inflow" else -1* round(value, 2)

        return result

#def flatten_cpf_summary(cpf):
#    print(f"\n📅 Date: {cpf.current_date}")
#
#    def print_section(title, data):
#        print(f"\n{title}:")
#        for k, v in data.items():
#            print(f"  - {k:<15}: {v:,.2f}")
#
#    print_section("Inflow", cpf.inflow)
#    print_section("Outflow", cpf.outflow)
    
def generate_cpf_projection():
    config_loader = ConfigLoader('cpf_config.json')
    cpf = CPFAccount(config_loader)
    cpf.current_date = datetime.strptime(config_loader.get('start_date'), "%Y-%m-%d")

    cpf.update_balance('oa', config_loader.get('oa_balance', 0), 'initial_oa_balance')
    cpf.update_balance('sa', config_loader.get('sa_balance', 0), 'initial_sa_balance')
    cpf.update_balance('ma', config_loader.get('ma_balance', 0), 'initial_ma_balance')
    cpf.update_balance('ra', config_loader.get('ra_balance', 0), 'initial_ra_balance')
    cpf.update_balance('excess', config_loader.get('excess_balance', 0), 'initial_excess_balance')
    cpf.update_balance('loan', config_loader.get('loan_balance', 0), 'initial_loan_balance')
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
            cpf.transfer_to_ra()  # Transfer to RA                                            
                                                                                                 
            # Step 4: Mark SA as closed
            sa_closed = True
            
        # Skip operations on SA if it is closed
        if sa_closed:
            cpf.sa_balance = (0, "SA account is closed")

        # CPF allocation logic - Skip SA if closed
        for account in ['oa', 'ma', 'sa'] if age < 55 and not sa_closed else ['oa', 'ma', 'ra']:
            if account == 'sa' and sa_closed:
                continue
            allocation = cpf.calculate_cpf_allocation(age=age, salary=salary, account=account, config=config_loader)
           # cpf.record_inflow(account=account, amount=allocation, message=f'allocation_{account}')
            cpf.update_balance(account, allocation, f'allocation_{account}')

        # BRS payouts at age 67+
        if age >= 67:
            brs_payout = config_loader.get('retirement_sums', {}).get('brs', {}).get('payout', 0)
          #  cpf.record_inflow('excess', brs_payout, f'brs_payout_{age}')
            cpf.update_balance('excess', brs_payout, f'brs_payout_{age}')

        # Apply interest at the end of the year
        if cpf.current_date.month == 12:
            # Skip SA interest if closed
            for account in ['oa', 'ma', 'ra', 'sa']:
                if account == 'sa' and sa_closed:
                    continue
                interest_rate = config_loader.get('interest_rates', {}).get(account, 2.5)
                balance = getattr(cpf, f'_{account}_balance')
                if balance > 0:
                   # cpf.record_inflow(account, balance * (interest_rate / 100 / 12), 'interest')
                    cpf.update_balance(account, balance * (interest_rate / 100 / 12), 'interest')
        # Loan payment logic

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
            cpf.record_inflow(account=account, amount=allocation, message=f'allocation_{account}')
        # Apply interest at the end of the year
        if cpf.current_date.month == 12:
            cpf.apply_interest(age=age)
        # CPF payout
        cpf_payout = cpf.calculate_cpf_payout(age=age)
        cpf.record_inflow(account='excess', amount=cpf_payout, message=f'cpf_payout_{age}')

       # Loan payment logic
        if age < 55 :
           loan_payments = config_loader.get('loan_payments', {})
           loan_payment = loan_payments.get('year_1_2', 0) if age < 24 else loan_payments.get('year_3', 0)
           loan_payment = min(loan_payment, cpf.loan_balance[0])
           cpf.loan_balance = (cpf.loan_balance[0] - loan_payment, "loan_payment")

        # CPF Transfer of funds at the age of 55
        if age == 55 and cpf.current_date.month == 7:
            cpf.transfer_to_ra() # ntransfer to EXCESS_BALANCE not RA
            cpf.loan_balance = (0, "loan_payment")
            cpf._sa_balance = 0
            cpf._sa_message = "SA balance zeroed out after transfer to RA and Excess Balance"
           # cpf.excess_balance = (cpf.oa_balance[0] + cpf.sa_balance[0], "transfer_to_excess")
           # cpf.excess_balance ``                                                

        # Display balances
        print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{cpf.sa_balance[0]:<15,.2f}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{cpf_payout:<12,.2f}")
       
       
            
        if( age == 55 and cpf.current_date.month == 7) or (age == 55 and cpf.current_date.month == 8):
            flattened_dict = flatten_cpf_summary_as_dict(cpf)
            pprint(flattened_dict)
            
            
        
if __name__ == "__main__":
    main()