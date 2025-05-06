import unittest
import json
import os
import subprocess  # Import the subprocess module

class TestConfigFile(unittest.TestCase):
    
    def setUp(self):
        # Define file paths
        self.input_file = 'xcpf_config.json'
        self.output_file = 'cpf_config.json'
        self.script_path = 'src/cpf_program_v9.py'  # Path to the script

    def tearDown(self):
        # Clean up: remove the created files if they exist
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
    
    def test_config_file_creation(self):
        # Create a dummy input file for testing
        dummy_data = {"key1": "value1", "key2": 123}
        with open(self.input_file, 'w') as f:
            json.dump(dummy_data, f, indent=4)
        
        # Run the script as a subprocess, passing input and output file paths as arguments
        result = subprocess.run(['python', self.script_path, self.input_file, self.output_file], capture_output=True, text=True)
        
        # Check if the script ran without errors
        self.assertEqual(result.returncode, 0, f"Script failed with error: {result.stderr}")
        
        # Check if the output file is created
        self.assertTrue(os.path.exists(self.output_file))
        
        # Read the content of the output file and compare with the expected output
        with open(self.output_file, 'r') as f:
            output_data = json.load(f)
        
        # Verify the output matches the expected transformation logic in v9
        self.assertEqual(dummy_data, output_data)

    def test_reconcile_cpf_logs(self):
        # Define the path to the CPF logs file
        cpf_logs_file = 'cpf_logs20250507.json'

        # Load the CPF logs
        with open(cpf_logs_file, 'r') as f:
            logs = [json.loads(line) for line in f]

        # Reconcile the logs by checking balances
        accounts = {}
        for log in logs:
            account = log['account']
            new_balance = log['new_balance']
            if account in accounts:
                self.assertEqual(accounts[account], log['old_balance'], f"Mismatch in {account} balance")
            accounts[account] = new_balance

        # Ensure all accounts have been reconciled
        for account, balance in accounts.items():
            self.assertIsNotNone(balance, f"Account {account} has no final balance")

if __name__ == '__main__':
    unittest.main()
