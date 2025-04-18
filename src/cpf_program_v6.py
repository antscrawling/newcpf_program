import atexit
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from pprint import pprint
#from dateutility import  MyDateDictGenerator
import json
from cpf_config_loader_v2 import ConfigLoader
from reconfigure_date import MyDateTime

from collections import OrderedDict
import inspect
from multiprocessing import Process, Queue
from queue import Empty

# Load configuration
config = ConfigLoader('cpf_config.json')


class CPFAccount:
    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader
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
        self.log_workers = []
        self.cache = []  # Cache for batching logs
        self.cache_limit = 10  # Number of logs to batch before writing

        # Start multiple worker processes
        for i in range(2):  # Number of workers
            worker = Process(target=self._save_log_worker, args=(self.log_queue, f'logs_worker_{i}.json'))
            worker.daemon = True  # Ensure the process terminates with the main program
            worker.start()
            self.log_workers.append(worker)

    def _save_log_worker(self, queue, filename):
        """Worker process to save logs to a file."""
        with open(filename, 'a') as file:
            while True:
                try:
                    log_entry = queue.get(timeout=1)  # Wait for a log entry with a timeout
                    if log_entry == "STOP":
                        break
                    file.write(json.dumps(log_entry, default=self.custom_serializer) + '\n')
                except Empty:
                    continue  # Handle timeout gracefully
                except Exception as e:
                    pass

    def save_log_to_file(self, log_entry):
        """Cache log entries and send them to the worker process in batches."""
        self.cache.append(log_entry)
        if len(self.cache) >= self.cache_limit:
            self.flush_cache()  # Flush when limit is reached

    def flush_cache(self):
        """Flush any remaining logs in the cache to the queue."""
        try:
            for entry in self.cache:
                if self.log_queue:
                    self.log_queue.put(entry)
            self.cache = []
        except Exception as e:
            pass

    def close_log_writer(self):
        """Stop all log writer processes."""
        self.flush_cache()  # Ensure all cached logs are sent to the queue
        try:
            if self.log_queue:
                for _ in self.log_workers:
                    self.log_queue.put("STOP")  # Send the stop signal to each worker
        except Exception as e:
            pass
        finally:
            for worker in self.log_workers:
                try:
                    worker.join(timeout=2)  # Reduced timeout slightly
                except Exception as e:
                    pass
            self.log_queue = None
            self.log_workers = []

    def custom_serializer(self, obj):
        """Custom serializer for non-serializable objects like datetime."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

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

        # Save the log entry using caching and multiprocessing
        self.save_log_to_file(log_entry)

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and ensure resources are released."""
        self.close_log_writer()
        return False

    def get_date_dict(self, start_date, end_date, birth_date):
        """Generate a date dictionary."""
        print("Warning: get_date_dict needs implementation in CPFAccount or be imported correctly.")
        from cpf_date_generator_v2 import generate_date_dict
        return generate_date_dict(start_date, end_date, birth_date)

    def update_balance(self, account, amount, message):
        """Update account balance and log the change."""
        current_balance, _ = getattr(self, f"{account}_balance")
        setattr(self, f"{account}_balance", (current_balance + amount, message))

    def calculate_cpf_allocation(self, age, salary, account, config):
        """Calculate CPF allocation."""
        print(f"Warning: calculate_cpf_allocation needs implementation in CPFAccount.")
        return 0.0

    def apply_interest(self, age):
        """Apply interest to CPF accounts."""
        print(f"Warning: apply_interest needs implementation in CPFAccount.")
        pass

    def calculate_cpf_payout(self, age):
        """Calculate CPF payout."""
        print(f"Warning: calculate_cpf_payout needs implementation in CPFAccount.")
        return 0.0

    def transfer_to_ra(self):
        """Transfer funds to RA."""
        print(f"Warning: transfer_to_ra needs implementation in CPFAccount.")
        pass

