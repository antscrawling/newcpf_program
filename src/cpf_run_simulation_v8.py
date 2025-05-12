from cpf_config_loader_v10 import ConfigLoader
from cpf_program_v11 import CPFAccount
from tqdm import tqdm  # For the progress bar
from cpf_date_generator_v3 import DateGenerator
import os
import sqlite3
import json
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# Dynamically determine the src directory
SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to the src directory
CONFIG_FILENAME = os.path.join(SRC_DIR, 'cpf_config.json')  # Full path to the config file
DATABASE_NAME = os.path.join(SRC_DIR, 'cpf_simulation.db')  # Full path to the database file
DATE_KEYS = ['start_date', 'end_date', 'birth_date']
DATE_FORMAT = "%Y-%m-%d"

# Load the configuration file
config_loader = ConfigLoader(CONFIG_FILENAME)

def create_connection():
    """Creates a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """Creates a table to store CPF simulation data."""
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS cpf_data (
            date_key TEXT PRIMARY KEY,
            dbreference INTEGER,
            age INTEGER,
            oa_balance REAL,
            sa_balance REAL,
            ma_balance REAL,
            ra_balance REAL,
            loan_balance REAL,
            excess_balance REAL,
            cpf_payout REAL,
            message TEXT
        );
        """
        cur = conn.cursor()
        cur.execute(sql)
    except sqlite3.Error as e:
        print(e)

def loan_computation_first_three_years(cpf):
    # Corrected implementation for loan_payments
    loan_payments = cpf.config.getdata('loan_payments', {})
    payment_key = 'year_1_2' if cpf.age < 24 else 'year_3'
    float(loan_payments.getdata(payment_key, 0.0)) if payment_key in loan_payments else 0.0

def compute_age(start_date : datetime.date, birth_date : datetime.date) -> int:
    """
    Compute the age based on the start date and birth date.
    The age increments by 1 every July 6.
    """
    # Calculate the base age
    base_age = relativedelta(start_date, birth_date).years
    #if start_date.month >= birth_date.month:
    #    base_age += 1
    return  base_age
                
                
def main(dicct: dict[str, dict[str, dict[str, float]]] = None):
    # Step 1: Load the configuration
    oa_bal = 0.0
    sa_bal = 0.0
    ma_bal = 0.0
    ra_bal = 0.0
    excess_bal = 0.0
    loan_bal = 0.0
    config_loader = ConfigLoader('cpf_config.json')
    start_date = config_loader.getdata('start_date', {})
    end_date = config_loader.getdata('end_date', {})
    birth_date = config_loader.getdata('birth_date', {})
    payout_type = config_loader.getdata('payout_type',{})
    retirement_amount = config_loader.getdata(['retirement_sums',payout_type,'amount'], 0)
    
    # Validate that the dates are loaded correctly
    if not all([start_date, end_date, birth_date]):
        raise ValueError("Missing required date values in the configuration file. Please check 'start_date', 'end_date', and 'birth_date'.")

    # Step 2: Generate the date dictionary
    dategen = DateGenerator(start_date=start_date, end_date=end_date, birth_date=birth_date)
    date_dict = dategen.generate_date_dict()
    dategen.save_file(dategen.date_list, format='csv')  # Save the date_dict to file after generation
   # print(f"Generated date_dict with {len(date_dict)} entries.")
    if not date_dict:
        print("Error: date_dict is empty. Loop will not run.")
        return  # Exit if empty

    is_initial = True
    is_display_special_july = False
    # Step 4: Calculate CPF per month using CPFAccount
    with CPFAccount(config_loader) as cpf:
        # this method will update the cpf_config.json with the amounts needed in allocation.
        cpf.start_date = cpf.convert_date_strings(key='start_date', date_str=start_date)
        cpf.end_date = cpf.convert_date_strings(key='end_date', date_str=end_date)
        cpf.birth_date = cpf.convert_date_strings(key='birth_date', date_str=birth_date)
        cpf.current_date =  cpf.start_date
        cpf.age = compute_age(cpf.start_date, cpf.birth_date)
        cpf.date_key = cpf.current_date.strftime('%Y-%m')
        
        #step 1 before iteration starts.
        cpf.compute_and_add_allocation()
        #print headers
        # Violet color ANSI escape code
        violet = "\033[35m"
        reset = "\033[0m"  # Reset color to default

        print(f"{violet}{'Simulation of CPF Data':^150}{reset}")
        print(f"{violet}====================================={reset}")
        print(f"{violet}== Start Date: {cpf.start_date}{reset}")
        print(f"{violet}== End Date: {cpf.end_date}{reset}")
        print(f"{violet}== Birth Date: {cpf.birth_date}{reset}")
        print(f"{violet}== Age: {cpf.age}{reset}")
        print(f"{violet}== Retirement Amount: {retirement_amount}{reset}")
        print(f"{violet}== OA Balance Amount: {oa_bal}{reset}")
        print(f"{violet}== SA Balance Amount: {sa_bal}{reset}")
        print(f"{violet}== MA Balance Amount: {ma_bal}{reset}")
        print(f"{violet}== Loan Balance Amount: {loan_bal}{reset}")
        print(f"{violet}======================================{reset}")
        print(f"{violet}{'-' * 150}{reset}")
        #step 2 print the headers
        print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
        print("-" * 150)

        #step 3 determine if inital balance is needed.
        if is_initial:
            print("Loading initial balances from config...")
            # Use property setters to ensure logging                                                                                                            
            #step 4 set the initial balances
           
            initoa_balance = float(cpf.config.getdata('oa_balance', 0.0))
            initsa_balance = float(cpf.config.getdata('sa_balance', 0.0))
            initma_balance = float(cpf.config.getdata('ma_balance', 0.0))
            initra_balance = float(cpf.config.getdata('ra_balance', 0.0))
            initexcess_balance = float(cpf.config.getdata('excess_balance', 0.0))
            initloan_balance = float(cpf.config.getdata('loan_balance', 0.0))
            #record the updates
            for account, new_balance in zip(['oa', 'sa', 'ma', 'ra', 'excess', 'loan'], [initoa_balance, initsa_balance, initma_balance, initra_balance, initexcess_balance, initloan_balance]):
                cpf.record_inflow(account=account, amount=new_balance, message=f"Initial Balance of {account}")
            is_initial = False
            
       #  get loan payments from config
        loan_paymenty1 = float(cpf.config.getdata(['loan_payments','year_1_2'], 0.0))         
        loan_paymenty3 = float(cpf.config.getdata(['loan_payments','year_3'], 0.0))
        loan_paymenty4 = float(cpf.config.getdata(['loan_payments','year_4_beyond'], 0.0))     
       
       
       #  calculate the allocations outside the loop                                                                                 
        year = 1
        # CPF allocation logic
        with create_connection() as conn:
            create_table(conn)
            ###################################################################################
            # LOOP STARTS HERE
            ###################################################################################
            #print(date_dict)
            for date_key, date_info in tqdm(date_dict.items(), desc="Processing CPF Data", unit="month", colour="blue"):
                #stop when cpf._ra_balance == 0.0
                
                
                
                # add counter
                cpf.dbreference = cpf.add_db_reference()
                cpf.date_key = date_key
                cpf.current_date = date_dict[date_key]['period_end']
                cpf.age = compute_age(cpf.current_date, cpf.birth_date)
              
                #cpf.current_date = date_info['period_end']
                
                # loan payments
                
                if year == 1 and cpf._loan_balance > 0:
                    cpf.record_outflow(account='oa',   amount=loan_paymenty1, message=f"Loan payment from OA Account at year 1 age {cpf.age}")
                    cpf.record_outflow(account='loan', amount=loan_paymenty1, message=f"Loan payment from OA Account at year 1 age {cpf.age}")
                elif year == 2 and cpf._loan_balance > 0:
                    cpf.record_outflow(account='oa',   amount=loan_paymenty1, message=f"Loan payment from OA Account at year 2 age {cpf.age}")
                    cpf.record_outflow(account='loan', amount=loan_paymenty1, message=f"Loan payment from OA Account at year 2 age {cpf.age}")
                elif year == 3 and cpf._loan_balance > 0:
                    cpf.record_outflow(account='oa',   amount=loan_paymenty3, message=f"Loan payment from OA Account at year 3 age {cpf.age}")
                    cpf.record_outflow(account='loan', amount=loan_paymenty3, message=f"Loan payment from OA Account at year 3 age {cpf.age}")
                elif year >= 4 and cpf._loan_balance > 0:
                   
                    if cpf._loan_balance > 0:
                        loan_payment = min(loan_paymenty4, cpf._loan_balance)
                        cpf.record_outflow(account='oa', amount=loan_payment, message=f"Loan payment from OA Account at year 4, age {cpf.age}")
                        cpf.record_outflow(account='loan', amount=loan_payment, message=f"Loan payment from OA Account at year 4, age {cpf.age}")
                    elif cpf._loan_balance < 3000:
                        loan_payment = min(loan_paymenty4, cpf._loan_balance)
                    else:
                        cpf.loan_balance = 0.0
                year += 1
                # Increment the year counter           
                if cpf.age < 55:    
                    cpf.record_inflow(account='oa', amount=(dicct['allocation_below_55']['oa']['amount']).__round__(2), message=f"Allocation for OA at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=(dicct['allocation_below_55']['sa']['amount']).__round__(2), message=f"Allocation for SA at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=(dicct['allocation_below_55']['ma']['amount']).__round__(2), message=f"Allocation for MA at age {cpf.age}")

                elif cpf.age == 55 and cpf.current_date.month == cpf.birth_date.month :
                          
                    cpf.record_inflow(account='oa', amount=(dicct['allocation_below_55']['oa']['amount']).__round__(2), message=f"Allocation for OA at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=(dicct['allocation_below_55']['sa']['amount']).__round__(2), message=f"Allocation for SA at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=(dicct['allocation_below_55']['ma']['amount']).__round__(2), message=f"Allocation for MA at age {cpf.age}")
                else:
                    if 55 <= cpf.age < 60  and cpf.current_date.month >=8 :                              
                        age_key = '56_to_60'
                    if 60 <= cpf.age < 65:
                        age_key = '61_to_65'
                    if 65 <= cpf.age < 70:
                        age_key = '66_to_70'
                    else:
                        age_key = 'above_70'

                    # Get the allocation amounts from the config
                    for account in ['oa', 'ma', 'ra']:
                        #if cpf.current_date.month == 7 and cpf.age == 55 and account  == 'ra':
                        #    account = 'sa'
                        #elif cpf.current_date.month == 8 and cpf.age == 55 and account  == 'sa':
                        #    account = 'ra'
                        #else: 
                        #    account = account
                        allocation_amount = cpf.config.getdata(['allocation_above_55',account,age_key,'amount'],0 ) # dicct.get('allocation_above_55',{}).get(account,{}).get(age_key,{}).get('amount', 0.0))
                        cpf.record_inflow(account=account, amount=allocation_amount.__round__(2), message=f"Allocation for {account} at age {cpf.age}")
                                                         
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
                        cpf.message = f"Applying interest for {account} at age {cpf.age}"
                        account_balance = getattr(cpf, f'_{account}_balance', 0.0)
                        if account_balance > 0:
                            if account == 'oa':
                                #account: str, age: int, amount: float):
                                oa_interest = round(cpf.calculate_interest_on_cpf(account=account,  amount=account_balance),2)
                            elif account == 'sa':
                                sa_interest = round(cpf.calculate_interest_on_cpf(account=account,  amount=account_balance),2)
                            elif account == 'ma':
                                ma_interest = cpf.calculate_interest_on_cpf(account=account,  amount=account_balance).__round__(2)
                            elif account == 'ra':
                                ra_interest = cpf.calculate_interest_on_cpf(account=account,  amount=account_balance).__round__(2)
                            # Record the interest inflow                                                       
                    oa_extra_interest, sa_extra_interest, ma_extra_interest, ra_extra_interest = cpf.calculate_extra_interest()
                    cpf.record_inflow(account='oa', amount=oa_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=sa_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=ma_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ra', amount=ra_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='oa', amount=oa_extra_interest.__round__(2), message=f"Extra Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=sa_extra_interest.__round__(2), message=f"Extra Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=ma_extra_interest.__round__(2), message=f"Extra Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ra', amount=ra_extra_interest.__round__(2), message=f"Extra Interest for {account} at age {cpf.age}")                                                                                                

                # CPF payout calculation
                
                if hasattr(cpf, 'calculate_cpf_payout'):
                    cpf.payout = cpf.calculate_cpf_payout(payout_type) 
                    if isinstance(cpf.payout, (int, float)):
                        cpf.payout = max(min(cpf.payout, cpf._ra_balance),0.00)
                        setattr(cpf, 'payout', cpf.payout)
                        if cpf._ra_balance > 0:
                            cpf.record_outflow(account='ra',   amount=cpf.payout, message=f"CPF payout at age {cpf.age}")
                            cpf.record_inflow(account='excess',amount=cpf.payout, message=f"CPF payout at age {cpf.age}")
                        else:
                            cpf.payout = 0.0
                       
                if cpf._ra_balance == 0.0 and cpf.age > 55:
                    print(f"Stopping simulation at age {cpf.age} as RA balance is zero.")
                    break


                # Display balances including July 2029
                cpf.date_key = date_key
                oa_bal = getattr(cpf, '_oa_balance', 0.0).__round__(2)
                sa_bal = getattr(cpf, '_sa_balance', 0.0).__round__(2)
                ma_bal = getattr(cpf, '_ma_balance', 0.0).__round__(2)
                ra_bal = getattr(cpf, '_ra_balance', 0.0).__round__(2)
                loan_bal = getattr(cpf, '_loan_balance', 0.0).__round__(2)
                excess_bal = getattr(cpf, '_excess_balance', 0.0).__round__(2)
                payout = getattr(cpf, 'payout', 0.0).__round__(2)
               # display_ra = f"{'closed':<15}" if cpf._sa_balance == 0.0 else f'{float(sa_bal):<15,.2f}'
                print(f"{date_key:<15}{cpf.age:<5}"
                      f"{float(oa_bal):<15,.2f}{float(sa_bal):<15,.2f}"
                      f"{float(ma_bal):<15,.2f}{float(ra_bal):<15,.2f}"
                      f"{float(loan_bal):<12,.2f}{float(excess_bal):<12,.2f}"
                      f"{float(cpf.payout):<12,.2f}")
                
                
                

                if cpf.age == 55 and cpf.current_date.month == cpf.birth_date.month :
                    is_display_special_july = True
                    orig_oa_bal = oa_bal
                    orig_sa_bal = sa_bal
                    orig_ma_bal = ma_bal
                    orig_loan_bal = loan_bal
                    orig_cpf_payout = payout
                
                                          
                if is_display_special_july:    
                    # Special printing for age 55 and month 7
                    display_date_key = f"{date_key}-cpf"
                    display_oa_bal = -orig_oa_bal
                    display_sa_bal = -orig_sa_bal
                    display_ma_bal = orig_ma_bal
                    display_loan_bal = -orig_loan_bal if loan_bal > 0 else 0.0             
                    display_ra_bal =  retirement_amount
                    display_excess_bal = (orig_oa_bal + orig_sa_bal - orig_loan_bal - retirement_amount)
                    display_cpf_payout = orig_cpf_payout
                    ##                                   
                    print(f"{display_date_key:<15}{cpf.age:<4}"
                          f"{float(display_oa_bal):<15,.2f}{display_sa_bal:<15,.2f}"
                          f"={float(display_ma_bal):<14,.2f}+{float(display_ra_bal):<14,.2f}"
                          f"{float(display_loan_bal):<13,.2f}{float(display_excess_bal):<12,.2f}"
                          f"{float(display_cpf_payout):<12,.2f}")

                    cpf.record_inflow(account= 'oa',  amount= display_oa_bal,  message= f"transfer_cpf_age={cpf.age}")
                    cpf.record_inflow(account= 'sa',  amount= display_sa_bal,  message= f"transfer_cpf_age={cpf.age}")
                    cpf.record_inflow(account= 'loan',amount= display_loan_bal,message= f"transfer_cpf_age={cpf.age}")
                    cpf.record_inflow(account= 'ra',  amount= display_ra_bal,  message= f"transfer_cpf_age={cpf.age}")
                    cpf.record_inflow(account= 'excess',amount= display_excess_bal,message= f"transfer_cpf_age={cpf.age}")
                    is_display_special_july = False   
                # Insert data into the database for every iteration
                if cpf.age == 55 :
                    cpf.message = f"Age 55 - Special case for CPF payout"
                elif cpf._ra_balance == 0.0 and cpf.age >= 55:
                    cpf.message = f"Age {cpf.age} - RA balance is zero"
                elif  cpf.age == 67:
                    cpf.message = f"Age {cpf.age} - CPF payout"
                elif cpf.current_date.month == 12:
                    cpf.message = f"End of year {cpf.age} - CPF Interest"
                else :
                    cpf.message = f"Age {cpf.age} - Regular CPF calculation" 
                if not is_display_special_july:
                    cpf.insert_data(conn, str(date_key),int(cpf.dbreference) ,int(cpf.age), float(oa_bal), float(sa_bal), float(ma_bal), float(ra_bal), float(loan_bal), float(excess_bal), float(payout),str(cpf.message))
                    a=0
            # Pass birth_date as a string
           # display_data_from_db()  # Remove the argument
    #this transforms the logs from json to csv.

def display_data_from_db():
    """Displays CPF data from the database for monthly data between 2025-05 and 2061-12."""
    conn = create_connection()
    cur = conn.cursor()

    # Define the date range for monthly data
    start_date = "2025-05-01"
    end_date = "2061-12-31"

    # Query the database for all monthly data within the specified range
    sql = f"""
        SELECT date_key, dbreference, age, oa_balance, sa_balance, ma_balance, ra_balance, loan_balance, excess_balance, cpf_payout, message
        FROM cpf_data
        WHERE date_key BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date_key;  -- Ensure all months are retrieved
    """

    cur.execute(sql)
    cur.fetchall()

    conn.close()

if __name__ == "__main__":
    # Load the configuration file
    config_loader = ConfigLoader(CONFIG_FILENAME)
    # Load the configuration data
    config_loader.data  = config_loader.getdata()
    # Extract keys and values from the configuration data
    keys, values = config_loader.get_keys_and_values()
    
    # Create a dictionary to hold the allocation data
    allocation_data = {
        'allocation_below_55': {
            'oa': {'allocation': 0.0, 'amount': 0.0},
            'sa': {'allocation': 0.0, 'amount': 0.0},
            'ma': {'allocation': 0.0, 'amount': 0.0},
        },
        'allocation_above_55': {
            'oa': {'allocation': 0.0, 'amount': 0.0},
            'sa': {'allocation': 0.0, 'amount': 0.0},
            'ma': {'allocation': 0.0, 'amount': 0.0},
            'ra': {'allocation': 0.0, 'amount': 0.0},
        }
    }
    
    # Call the main function with the allocation data
    main(allocation_data)















































































