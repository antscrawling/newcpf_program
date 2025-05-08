from cpf_config_loader_v4 import ConfigLoader
from cpf_program_v9 import CPFAccount
from tqdm import tqdm  # For the progress bar
from cpf_date_generator_v4 import DateGenerator
import os
import sqlite3
from pydantic import BaseModel  # Import BaseModel
import json

# Load the configuration file
with open("cpf_config.json", "r") as f:
    config_data = json.load(f)

## Define Pydantic models based on the structure of the config data
#class Allocation(BaseModel):
#    allocation: float
#    amount: float
#
#class AgeAllocation(BaseModel):
#    allocation: float
#    amount: float
#
#class OaAllocationAbove55(BaseModel):
#    _56_to_60: AgeAllocation
#    _61_to_65: AgeAllocation
#    _66_to_70: AgeAllocation
#    above_70: AgeAllocation
#
#class MaAllocationAbove55(BaseModel):
#    _56_to_60: AgeAllocation
#    _61_to_65: AgeAllocation
#    _66_to_70: AgeAllocation
#    above_70: AgeAllocation
#
#class RaAllocationAbove55(BaseModel):
#    _56_to_60: AgeAllocation
#    _61_to_65: AgeAllocation
#    _66_to_70: AgeAllocation
#    above_70: AgeAllocation
#
#class AllocationBelow55(BaseModel):
#    oa: Allocation
#    sa: Allocation
#    ma: Allocation
#
#class AllocationAbove55(BaseModel):
#    oa: OaAllocationAbove55
#    sa: Allocation
#    ma: MaAllocationAbove55
#    ra: RaAllocationAbove55
#
#class InterestRates(BaseModel):
#    oa_below_55: float
#    oa_above_55: float
#    sa: float
#    ma: float
#    ra: float
#
#class ExtraInterest(BaseModel):
#    below_55: float
#    first_30k_above_55: float
#    next_30k_above_55: float
#
#class RetirementSumsAmount(BaseModel):
#    amount: float
#    payout: float
#
#class RetirementSums(BaseModel):
#    brs: RetirementSumsAmount
#    frs: RetirementSumsAmount
#    ers: RetirementSumsAmount
#
#class LoanPayments(BaseModel):
#    year_1_2: float
#    year_3: float
#    year_4_beyond: float
#
#class CpfContributionRates(BaseModel):
#    employee: float
#    employer: float
#
#class AgeBasedContributionRates(BaseModel):
#    below_55: CpfContributionRates
#    _55_to_60: CpfContributionRates
#    _60_to_65: CpfContributionRates
#    _65_to_70: CpfContributionRates
#    above_70: CpfContributionRates
#
#class ConfigModel(BaseModel):
#    allocation_below_55: AllocationBelow55
#    allocation_above_55: AllocationAbove55
#    cpf_payout_age: int
#    age_of_brs: int
#    start_date: str
#    end_date: str
#    birth_date: str
#    salary: int
#    loan_amount: int
#    interest_rates: InterestRates
#    extra_interest: ExtraInterest
#    retirement_sums: RetirementSums
#    oa_balance: float
#    sa_balance: float
#    ma_balance: float
#    ra_balance: float
#    excess_balance: float
#    loan_balance: float
#    loan_payments: LoanPayments
#    salary_cap: int
#    cpf_contribution_rates: AgeBasedContributionRates

# Database setup
DATABASE_NAME = 'cpf_simulation.db'

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
            age INTEGER,
            oa_balance REAL,
            sa_balance REAL,
            ma_balance REAL,
            ra_balance REAL,
            loan_balance REAL,
            excess_balance REAL,
            cpf_payout REAL
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

def import_log_file_and_save_to_sqlite(log_filepath: str, conn):
    """
    Import a log file and save its contents to the SQLite database.

    :param log_filepath: Path to the log file.
    :param conn: SQLite connection object.
    """
    with open(log_filepath, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)
                # Extract values from the log entry
                date_key = log_entry['date_key'].strftime("%Y-%m-%d")  # Convert to string format
                age = log_entry['age']
                oa_balance = log_entry['oa_balance']
                sa_balance = log_entry['sa_balance']
                ma_balance = log_entry['ma_balance']
                ra_balance = log_entry['ra_balance']
                loan_balance = log_entry['loan_balance']
                excess_balance = log_entry['excess_balance']
                cpf_payout = log_entry['cpf_payout']

                # Insert into the database
                sql = """
                INSERT OR REPLACE INTO cpf_data (date_key, age, oa_balance, sa_balance, ma_balance, ra_balance, loan_balance, excess_balance, cpf_payout)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """
                cur = conn.cursor()
                cur.execute(sql, (date_key, age, oa_balance, sa_balance, ma_balance, ra_balance, loan_balance, excess_balance, cpf_payout))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
                
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
    brs_amount = config_loader.getdata('retirement_sums', {}).get('brs', {}).get('amount', 0.0)    
   
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
        # this method will update the cpf_config.json with the amounts needed in allocation.
        #cpf.calculate_total_contributions()
        cpf.compute_and_add_allocation()
       
        print(f"{'Month and Year':<15}{'Age':<5}{'OA Balance':<15}{'SA Balance':<15}{'MA Balance':<15}{'RA Balance':<15}{'Loan Amount':<12}{'Excess Cash':<12}{'CPF Payout':<12}")
        print("-" * 150)


        if is_initial:
            print("Loading initial balances from config...")
            # Use property setters to ensure logging
            cpf.date_key = cpf.custom_serializer(cpf.current_date)
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
            
       #  calculate loan payments 
        loan_paymenty1 = float(cpf.config.getdata(['loan_payments','year_1_2'], 0.0))         
        loan_paymenty3 = float(cpf.config.getdata(['loan_payments','year_3'], 0.0))
        loan_paymenty4 = float(cpf.config.getdata(['loan_payments','year_4_beyond'], 0.0))     
       
       
       #  calculate the allocations outside the loop                                                                                 
        year = 1
        # CPF allocation logic
        with create_connection() as conn:
            create_table(conn)
            for date_key, date_info in tqdm(date_dict.items(), desc="Processing CPF Data", unit="month", colour="blue"):
           # for date_key in date_dict:
           
                cpf.date_key = date_key
                cpf.age = date_info['age']
                cpf.current_date = date_info['period_end']
                
                # loan payments
                
                if year == 1 and cpf._loan_balance > 0:
                    cpf.record_outflow(account='oa', amount=loan_paymenty1, message="Loan payment from OA Account at year 1")
                    cpf.record_outflow(account='loan', amount=loan_paymenty1, message="Loan payment from OA Account at year 1")
                elif year == 2 and cpf._loan_balance > 0:
                    cpf.record_outflow(account='oa', amount=loan_paymenty1, message="Loan payment from OA Account at year 2")
                    cpf.record_outflow(account='loan', amount=loan_paymenty1, message="Loan payment from OA Account at year 2")
                elif year == 3 and cpf._loan_balance > 0:
                    cpf.record_outflow(account='oa', amount=loan_paymenty3, message="Loan payment from OA Account at year 3")
                    cpf.record_outflow(account='loan', amount=loan_paymenty3, message="Loan payment from OA Account at year 3")
                elif year >= 4 and cpf._loan_balance > 0:
                    cpf.record_outflow(account='oa', amount=loan_paymenty4, message=f"Loan payment from OA Account at year 4, age {cpf.age}")
                    cpf.record_outflow(account='loan', amount=loan_paymenty4, message=f"Loan payment from OA Account at year 4, age {cpf.age}")
                year += 1
                # Increment the year counter           
                if cpf.age < 55:    
                    cpf.record_inflow(account='oa', amount=dicct['allocation_below_55']['oa']['amount'], message=f"Allocation for OA at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=dicct['allocation_below_55']['sa']['amount'], message=f"Allocation for SA at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=dicct['allocation_below_55']['ma']['amount'], message=f"Allocation for MA at age {cpf.age}")

                elif cpf.age == 55 and cpf.current_date.month == 7 and cpf.current_date.year  == 2029:
                          
                    cpf.record_inflow(account='oa', amount=dicct['allocation_below_55']['oa']['amount'], message=f"Allocation for OA at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=dicct['allocation_below_55']['sa']['amount'], message=f"Allocation for SA at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=dicct['allocation_below_55']['ma']['amount'], message=f"Allocation for MA at age {cpf.age}")
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
                        cpf.record_inflow(account=account, amount=allocation_amount, message=f"Allocation for {account} at age {cpf.age}")
                                                         
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
                                oa_interest = cpf.calculate_interest_on_cpf(account=account,  amount=account_balance)
                            elif account == 'sa':
                                sa_interest = cpf.calculate_interest_on_cpf(account=account,  amount=account_balance)
                            elif account == 'ma':
                                ma_interest = cpf.calculate_interest_on_cpf(account=account,  amount=account_balance)
                            elif account == 'ra':
                                ra_interest = cpf.calculate_interest_on_cpf(account=account,  amount=account_balance)
                            # Record the interest inflow                                                       
                    oa_extra_interest, sa_extra_interest, ma_extra_interest, ra_extra_interest = cpf.calculate_extra_interest()
                    cpf.record_inflow(account='oa', amount=oa_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=sa_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=ma_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ra', amount=ra_interest, message=f"Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='oa', amount=oa_extra_interest, message=f"Extra Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='sa', amount=sa_extra_interest, message=f"Extra Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ma', amount=ma_extra_interest, message=f"Extra Interest for {account} at age {cpf.age}")
                    cpf.record_inflow(account='ra', amount=ra_extra_interest, message=f"Extra Interest for {account} at age {cpf.age}")                                                                                                

                # CPF payout calculation
                cpf_payout = 0.0
                if hasattr(cpf, 'calculate_cpf_payout'):
                    payout_result = cpf.calculate_cpf_payout()
                    if isinstance(payout_result, (int, float)):
                        cpf_payout = payout_result
                        cpf.record_inflow('excess', cpf_payout, f"cpf_payout_{cpf.age}")



                # Display balances including July 2029
                cpf.date_key = date_key
                oa_bal = getattr(cpf, '_oa_balance', 0.0).__round__(2)
                sa_bal = getattr(cpf, '_sa_balance', 0.0).__round__(2)
                ma_bal = getattr(cpf, '_ma_balance', 0.0).__round__(2)
                ra_bal = getattr(cpf, '_ra_balance', 0.0).__round__(2)
                loan_bal = getattr(cpf, '_loan_balance', 0.0).__round__(2)
                excess_bal = getattr(cpf, '_excess_balance', 0.0).__round__(2)
               # display_ra = f"{'closed':<15}" if cpf._sa_balance == 0.0 else f'{float(sa_bal):<15,.2f}'
                print(f"{date_key:<15}{cpf.age:<5}"
                      f"{float(oa_bal):<15,.2f}{float(sa_bal):<15,.2f}"
                      f"{float(ma_bal):<15,.2f}{float(ra_bal):<15,.2f}"
                      f"{float(loan_bal):<12,.2f}{float(excess_bal):<12,.2f}"
                      f"{float(cpf_payout):<12,.2f}")
                
                
                

                if cpf.age == 55 and cpf.current_date.month == 7:
                    is_display_special_july = True
                    orig_oa_bal = oa_bal
                    orig_sa_bal = sa_bal
                    orig_ma_bal = ma_bal
                    orig_loan_bal = loan_bal
                
                                          
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
                cpf.insert_data(conn, date_key, cpf.age, oa_bal, sa_bal, ma_bal, ra_bal, loan_bal, excess_bal, cpf_payout)

            # Pass birth_date as a string
           # display_data_from_db()  # Remove the argument

def load_and_resave_log_as_json(log_filepath: str, output_json_filepath: str):
    """
    Load a log file and resave it as a JSON file.

    :param log_filepath: Path to the log file.
    :param output_json_filepath: Path to save the JSON file.
    """
    config_path = log_filepath
    output_path =  output_json_filepath
    if not os.path.exists(log_filepath):
        print(f"Log file '{log_filepath}' does not exist.")
        return

    try:
        
        import json
        from datetime import datetime, date
        with open(config_path, 'r') as f:
            # Attempt to load the entire file content as a single JSON object
            try:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = [logs]  # Ensure it's a list for consistent processing
            except json.JSONDecodeError:
                # If the file contains multiple JSON objects, load it line by line
                f.seek(0)  # Reset file pointer to the beginning
                logs = []
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Skipping invalid JSON line: {line.strip()} - {e}")
                        continue


        #convert list to dictionary
        for item in logs:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, (datetime, date)):
                        item[key] = value.strftime("%Y-%m-%d")
                    elif isinstance(value, list):
                        item[key] = [v.strftime("%Y-%m-%d") if isinstance(v, (datetime, date)) else v for v in value]
                    elif isinstance(value, str|int|float):
                       # item[key] = value
                        #try:
                        #    item[key] = datetime.strptime(value, "%Y-%m-%d").date()
                        #except ValueError:
                        #    pass  # not a date-formatted string
                        item[key] = value
        #logs = {log['account']: log for log in logs}    



        ##save using datasaver
        #ds = DataSaver(format='json')
        #for log in logs:
        #    ds.append(log)

        config_path = log_filepath
        output_path =  output_json_filepath

        with open(output_path, 'w') as f:
            json.dump(logs, f, default=str, indent=4)
        with open(output_path, 'r') as f:
            # Attempt to load the entire file content as a single JSON object
            try:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = [logs]  # Ensure it's a list for consistent processing
            except json.JSONDecodeError:
                # If the file contains multiple JSON objects, load it line by line
                f.seek(0)
        #import_log_file_and_save_to_sqlite(logs, create_connection())


    except Exception as e:
        print(f"Error processing log file: {e}")
        return

def display_data_from_db():
    """Displays CPF data from the database for monthly data between 2025-05 and 2061-12."""
    conn = create_connection()
    cur = conn.cursor()

    # Define the date range for monthly data
    start_date = "2025-05-01"
    end_date = "2061-12-31"

    # Query the database for all monthly data within the specified range
    sql = f"""
        SELECT date_key, age, oa_balance, sa_balance, ma_balance, ra_balance, loan_balance, excess_balance, cpf_payout
        FROM cpf_data
        WHERE date_key BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date_key;  -- Ensure all months are retrieved
    """

    cur.execute(sql)
    cur.fetchall()

    conn.close()

if __name__ == "__main__":
    mydict = {}
    mydict = {
    "allocation_below_55": {
        "oa": {
            "allocation": 0.6217,
            "amount": 1702.2146
        },
        "sa": {
            "allocation": 0.1621,
            "amount": 443.8298
        },
        "ma": {
            "allocation": 0.2162,
            "amount": 591.9556
        }
    },
    "allocation_above_55": {
        "oa": {
            "56_to_60": {
                "allocation": 0.3694,
                "amount": 1011.4172
            },
            "61_to_65": {
                "allocation": 0.149,
                "amount": 407.962
            },
            "66_to_70": {
                "allocation": 0.0607,
                "amount": 166.1966
            },
            "above_70": {
                "allocation": 0.08,
                "amount": 219.04
            }
        },
        "sa": {
            "allocation": 0.0,
            "amount": 0.0
        },
        "ma": {
            "56_to_60": {
                "allocation": 0.323,
                "amount": 884.374
            },
            "61_to_65": {
                "allocation": 0.4468,
                "amount": 1223.3383999999999
            },
            "66_to_70": {
                "allocation": 0.6363,
                "amount": 1742.1894
            },
            "above_70": {
                "allocation": 0.84,
                "amount": 2299.92
            }
        },
        "ra": {
            "56_to_60": {
                "allocation": 0.3076,
                "amount": 842.2088
            },
            "61_to_65": {
                "allocation": 0.4042,
                "amount": 1106.6996
            },
            "66_to_70": {
                "allocation": 0.303,
                "amount": 829.614
            },
            "above_70": {
                "allocation": 0.08,
                "amount": 219.04
            }
        }
    }
    }
    main(dicct = mydict)
    log_filepath = "cpf_logs.json"  # Replace with the actual log file pathfile path
    output_json_filepath = "cpf_logs_updated.json"  # Replace with the desired JSON file pathfile path
    # Create the file if it doesn't exist before calling the function
    if not os.path.exists(log_filepath):
        with open(log_filepath, 'w') as f:
            f.write('')  # Create an empty file
    load_and_resave_log_as_json(log_filepath, output_json_filepath)
   # import_log_file_and_save_to_sqlite('cpf_logs.json', create_connection())
    display_data_from_db()