from datetime import datetime
from dateutility import MyDateDictGenerator
import json

config = {
    "START_DATE": [2025, 4, 1],
    "END_DATE": [2060, 7, 31],
    "BIRTH_DATE": [1974, 7, 6],
    "OA_INTEREST_RATE_BELOW_55": 2.5,
    "OA_INTEREST_RATE_ABOVE_55": 4.0,
    "SA_INTEREST_RATE": 4.0,
    "MA_INTEREST_RATE": 4.0,
    "RA_INTEREST_RATE": 4.0,
    "EXTRA_INTEREST_BELOW_55": 1.0,
    "EXTRA_INTEREST_FIRST_30K_ABOVE_55": 2.0,
    "EXTRA_INTEREST_NEXT_30K_ABOVE_55": 1.0,
    "BASIC_RETIREMENT_SUM": {"amount": 106_500, "payout": 930},
    "FULL_RETIREMENT_SUM": {"amount": 213_000, "payout": 1_670},
    "ENHANCED_RETIREMENT_SUM": {"amount": 426_000, "payout": 3_300},
    "AGE_FOR_BRS_TRANSFER": {
        "age": 55,
        "month": 7,
        "year": 2029
    },
    "AGE_FOR_CPF_PAYOUT": 67,
    "CPF_PAYOUT_AMOUNT_BRS": 930,
    "CPF_PAYOUT_AMOUNT_FRS": 1670,
    "CPF_PAYOUT_AMOUNT_ERS": 3300,
    "CPF_PAYMENT_AMOUNT": 930,
    "SALARY_CAP": 7400,
    "SALARY_ALLOCATION_BELOW_55": {"oa": 0.23, "sa": 0.06, "ma": 0.08},
    "SALARY_ALLOCATION_ABOVE_55": {"oa": 0.115, "ra": 0.105, "ma": 0.075},
    "SALARY": 7000,
    "LOAN_PAYMENT_YEAR_1_2": 1687.39,
    "LOAN_PAYMENT_YEAR_3": 1782.27,
    "LOAN_PAYMENT_YEAR_4_BEYOND": 1817.49,
    "DATE_DICT_GENERATOR": None,
    "DATE_DICT": None,  # will be filled after instantiation
    "MONTH": 0,
    "CPF_CONTRIBUTION_RATES": {
        "below_55": {"employee": 0.20, "employer": 0.17},
        "55_to_60": {"employee": 0.15, "employer": 0.14},
        "60_to_65": {"employee": 0.09, "employer": 0.10},
        "65_to_70": {"employee": 0.075, "employer": 0.085},
        "above_70": {"employee": 0.05, "employer": 0.075}
    }
}

## Fill in DATE_DICT after generator is instantiated
#config["DATE_DICT"] = config["DATE_DICT_GENERATOR"].get_date_dict(
#    start_date=datetime(config["START_DATE"]),
#    birth_date=datetime(config["BIRTH_DATE"]),
#    end_date=datetime(config["END_DATE"])
#)


with open('config.json', 'w') as file:
    json.dump(config, file, indent=4)
    
