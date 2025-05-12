import unittest
import os
import json
import pandas as pd
from datetime import datetime
from cpf_config_loader_v10 import ConfigLoader
from cpf_program_v11 import CPFAccount
from cpf_build_reports_v1 import CPFLogEntry
from cpf_analysis_v1 import analyze_cpf_files
from cpf_run_simulation_v8 import main as run_simulation
import dicttoxml

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILENAME = os.path.join(SRC_DIR, 'cpf_config.json')
LOG_FILE_PATH = os.path.join(SRC_DIR, 'cpf_log_file.csv')
REPORT_FILE_PATH = os.path.join(SRC_DIR, 'cpf_report.csv')
MISMATCHES_FILE_PATH = os.path.join(SRC_DIR, 'cpf_mismatches.csv')
BALANCES_FILE_PATH = os.path.join(SRC_DIR, 'cpf_final_balances.csv')
XML_FILE_PATH = os.path.join(SRC_DIR, 'cpf_report.xml')


class TestCPFProgram(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        # Create a sample configuration file
        self.sample_config = {
            "allocation_below_55": {
                "oa": {"allocation": 0.6217, "amount": 1702.2146},
                "sa": {"allocation": 0.1621, "amount": 443.8298},
                "ma": {"allocation": 0.2162, "amount": 591.9556},
            },
            "cpf_payout_age": 67,
            "payout_type": "frs",
            "age_of_brs": 55,
            "salary_cap": 7400,
        }
        with open(CONFIG_FILENAME, "w") as f:
            json.dump(self.sample_config, f, indent=4)

    def tearDown(self):
        """Clean up test environment."""
        # Remove test files
        for file in [CONFIG_FILENAME, LOG_FILE_PATH, REPORT_FILE_PATH, MISMATCHES_FILE_PATH, BALANCES_FILE_PATH, XML_FILE_PATH]:
            if os.path.exists(file):
                os.remove(file)

    def test_save_configuration(self):
        """Test saving configuration."""
        config_loader = ConfigLoader(CONFIG_FILENAME)
        updated_config = {
            "cpf_payout_age": 70,
            "allocation_below_55": {
                "oa": {"allocation": 0.5, "amount": 1500.0},
                "sa": {"allocation": 0.3, "amount": 900.0},
                "ma": {"allocation": 0.2, "amount": 600.0},
            },
        }
        # Save the updated configuration
        with open(CONFIG_FILENAME, "w") as f:
            json.dump(updated_config, f, indent=4)

        # Reload and verify the configuration
        config_loader = ConfigLoader(CONFIG_FILENAME)
        self.assertEqual(config_loader.getdata(["cpf_payout_age"]), 70)
        self.assertEqual(config_loader.getdata(["allocation_below_55", "oa", "allocation"]), 0.5)

    def test_run_simulation(self):
        """Test running the CPF simulation."""
        # Run the simulation
        run_simulation()
        self.assertTrue(os.path.exists(LOG_FILE_PATH))

    def test_generate_csv_report(self):
        """Test generating a CSV report."""
        # Create a sample log file
        log_data = [
            {"date": "2025-05-01", "transaction_reference": 100000001, "age": 30, "account": "oa", "old_balance": 0.0,
             "new_balance": 1000.0, "amount": 1000.0, "type": "inflow", "message": "Initial inflow"},
            {"date": "2025-06-01", "transaction_reference": 100000002, "age": 30, "account": "oa", "old_balance": 1000.0,
             "new_balance": 500.0, "amount": -500.0, "type": "outflow", "message": "Test outflow"},
        ]
        pd.DataFrame(log_data).to_csv(LOG_FILE_PATH, index=False)

        # Build the report
        cpf_logs = CPFLogEntry(LOG_FILE_PATH)
        cpf_logs.build_report(output_format="csv")
        self.assertTrue(os.path.exists(REPORT_FILE_PATH))

    def test_run_analysis(self):
        """Test running the CPF analysis."""
        # Create sample log and report files
        log_data = [
            {"transaction_reference": 100000001, "amount": 1000.0, "account": "oa", "type": "inflow"},
            {"transaction_reference": 100000002, "amount": -500.0, "account": "oa", "type": "outflow"},
        ]
        report_data = [
            {"REF": 100000001, "ACCOUNT": "oa", "INFLOW": 1000.0, "OUTFLOW": 0.0},
            {"REF": 100000002, "ACCOUNT": "oa", "INFLOW": 0.0, "OUTFLOW": 500.0},
        ]
        pd.DataFrame(log_data).to_csv(LOG_FILE_PATH, index=False)
        pd.DataFrame(report_data).to_csv(REPORT_FILE_PATH, index=False)

        # Run the analysis
        analyze_cpf_files(LOG_FILE_PATH, REPORT_FILE_PATH, MISMATCHES_FILE_PATH, BALANCES_FILE_PATH)
        self.assertTrue(os.path.exists(MISMATCHES_FILE_PATH))
        self.assertTrue(os.path.exists(BALANCES_FILE_PATH))

    def test_download_xml(self):
        """Test downloading XML report."""
        # Create a sample report file
        report_data = [
            {"REF": 100000001, "ACCOUNT": "oa", "INFLOW": 1000.0, "OUTFLOW": 0.0},
            {"REF": 100000002, "ACCOUNT": "oa", "INFLOW": 0.0, "OUTFLOW": 500.0},
        ]
        pd.DataFrame(report_data).to_csv(REPORT_FILE_PATH, index=False)

        # Convert the report to XML
        report_df = pd.read_csv(REPORT_FILE_PATH)
        report_dict = report_df.to_dict(orient="records")
        xml_data = dicttoxml.dicttoxml(report_dict, custom_root="CPFReport", attr_type=False)

        # Save the XML file
        with open(XML_FILE_PATH, "wb") as f:
            f.write(xml_data)

        # Verify the XML file exists
        self.assertTrue(os.path.exists(XML_FILE_PATH))


if __name__ == "__main__":
    unittest.main()