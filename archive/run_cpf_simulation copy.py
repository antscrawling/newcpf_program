import atexit
from multiprocessing import Process, Queue
from cpf_config_loader_v2 import ConfigLoader
from archive.cpf_date_generator_v2 import generate_date_dict
from cpf_reconfigure_date_v2 import m
from datetime import datetime, timedelta
from pprint import pprint
import pandas as pd
from datetime import datetime, date
import inspect
import json
from tqdm import tqdm  # Import tqdm for the progress bar


class CPFAccount:
    def __init__(self, config_loader: ConfigLoader):  # Accept config_loader
        self.config = config_loader  # Store the config_loader instance
        self.current_date = datetime.now()

        # Account balances and logs
        self._oa_balance = 0.0
        self._oa_log = []
        self._oa_message = ""

        self._sa_balance = 0.0
        self._sa_log = []
        self._sa_message = ""

        self._ma_balance = 0.0
        self._ma_log = []
        self._ma_message = ""

        self._ra_balance = 0.0
        self._ra_log = []
        self._ra_message = ""

        self._excess_balance = 0.0
        self._excess_balance_log = []
        self._excess_message = ""

        self._loan_balance = 0.0
        self._loan_balance_log = []
        self._loan_message = ""

        # Log saving setup
        self.log_queue = Queue()
        self.log_process = Process(target=self._save_log_worker, args=(self.log_queue, 'logs.json'))
        self.log_process.daemon = True  # Ensure the process terminates with the main program
        self.log_process.start()

        # Register cleanup function
        atexit.register(self.close_log_writer)

    def _save_log_worker(self, queue, filename):
        """Worker process to save logs to a file."""
        with open(filename, 'a') as file:
            while True:
                try:
                    log_entry = queue.get(timeout=1)  # Wait for a log entry with a timeout
                    if log_entry == "STOP":
                        break
                    file.write(json.dumps(log_entry, default=self.custom_serializer) + '\n')
                except Exception:
                    continue  # Handle timeout or other exceptions gracefully

    def save_log_to_file(self, log_entry):
        """Send log entry to the worker process."""
        if self.log_process.is_alive():
            self.log_queue.put(log_entry)

    def close_log_writer(self):
        """Stop the log writer process."""
        if self.log_process.is_alive():
            self.log_queue.put("STOP")  # Send the stop signal
            self.log_process.join(timeout=5)  # Wait for the process to terminate

    def custom_serializer(self, obj):
        """Custom serializer for non-serializable objects like datetime."""
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        raise TypeError("Type not serializable")

    @property
    def sa_balance(self):
        return self._sa_balance, self._sa_message

    @sa_balance.setter
    def sa_balance(self, data):
        if isinstance(data, (tuple, list)) and len(data) == 2:
            value, message = data
        else:
            value, message = data, "no message"
        diff = value - self._sa_balance
        log_entry = {
            'date': self.current_date,
            'old_balance': self._sa_balance,
            'new_balance': value,
            'amount': diff,
            'type': 'inflow' if diff > 0 else 'outflow',
            'message': f'sa-{message}-{diff}'
        }
        self._sa_log.append(log_entry)
        self._sa_balance = value
        self._sa_message = message

        # Save the log entry using multiprocessing
        self.save_log_to_file(log_entry)

    # Similar property setters for `oa_balance`, `ma_balance`, `ra_balance`, `excess_balance`, and `loan_balance`

    def close(self):
        """Ensure the log writer process is properly closed."""
        self.close_log_writer()


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
    with CPFAccount(config_loader) as cpf:  # Use the context manager
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

        # Add a progress bar for the loop
        for date_key, date_info in tqdm(date_dict.items(), desc="Processing CPF Data", unit="month"):
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
                cpf.excess_balance = (cpf.oa_balance[0] + cpf.sa_balance[0], "transfer_to_excess")
                cpf.oa_balance = (0, "transfer_to_excess")
                cpf.sa_balance = (0, "transfer_to_excess")
                cpf._ra_balance += cpf.basic_retirement_sum
                cpf._excess_balance -= cpf.basic_retirement_sum
                cpf._excess_balance -= cpf.loan_balance[0]
                cpf.loan_balance = (0, "loan_full_payment")

            # Display balances
            print(f"{cpf.current_date.strftime('%b-%Y'):<15}{age:<5}{cpf.oa_balance[0]:<15,.2f}{cpf.sa_balance[0]:<15,.2f}{cpf.ma_balance[0]:<15,.2f}{cpf.ra_balance[0]:<15,.2f}{cpf.loan_balance[0]:<12,.2f}{cpf.excess_balance[0]:<12,.2f}{cpf_payout:<12,.2f}")


if __name__ == "__main__":
    main()

