from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import json

# Load the configuration file
with open("src/cpf_config.json", "r") as f:
    config_data = json.load(f)

# Define Pydantic models based on the structure of the config data
class Allocation(BaseModel):
    allocation: float
    amount: float

class AgeAllocation(BaseModel):
    allocation: float
    amount: float

class OaAllocationAbove55(BaseModel):
    _56_to_60: AgeAllocation
    _61_to_65: AgeAllocation
    _66_to_70: AgeAllocation
    above_70: AgeAllocation

class MaAllocationAbove55(BaseModel):
    _56_to_60: AgeAllocation
    _61_to_65: AgeAllocation
    _66_to_70: AgeAllocation
    above_70: AgeAllocation

class RaAllocationAbove55(BaseModel):
    _56_to_60: AgeAllocation
    _61_to_65: AgeAllocation
    _66_to_70: AgeAllocation
    above_70: AgeAllocation

class AllocationBelow55(BaseModel):
    oa: Allocation
    sa: Allocation
    ma: Allocation

class AllocationAbove55(BaseModel):
    oa: OaAllocationAbove55
    sa: Allocation
    ma: MaAllocationAbove55
    ra: RaAllocationAbove55

class InterestRates(BaseModel):
    oa_below_55: float
    oa_above_55: float
    sa: float
    ma: float
    ra: float

class ExtraInterest(BaseModel):
    below_55: float
    first_30k_above_55: float
    next_30k_above_55: float

class RetirementSumsAmount(BaseModel):
    amount: float
    payout: float

class RetirementSums(BaseModel):
    brs: RetirementSumsAmount
    frs: RetirementSumsAmount
    ers: RetirementSumsAmount

class LoanPayments(BaseModel):
    year_1_2: float
    year_3: float
    year_4_beyond: float

class CpfContributionRates(BaseModel):
    employee: float
    employer: float

class AgeBasedContributionRates(BaseModel):
    below_55: CpfContributionRates
    _55_to_60: CpfContributionRates
    _60_to_65: CpfContributionRates
    _65_to_70: CpfContributionRates
    above_70: CpfContributionRates

class ConfigModel(BaseModel):
    allocation_below_55: AllocationBelow55
    allocation_above_55: AllocationAbove55
    cpf_payout_age: int
    age_of_brs: int
    start_date: str
    end_date: str
    birth_date: str
    salary: int
    loan_amount: int
    interest_rates: InterestRates
    extra_interest: ExtraInterest
    retirement_sums: RetirementSums
    oa_balance: float
    sa_balance: float
    ma_balance: float
    ra_balance: float
    excess_balance: float
    loan_balance: float
    loan_payments: LoanPayments
    salary_cap: int
    cpf_contribution_rates: AgeBasedContributionRates

# Create a FastAPI instance
app = FastAPI()

# Define an API endpoint to return the configuration
@app.get("/config")
async def get_config() -> ConfigModel:
    return ConfigModel(**config_data)
