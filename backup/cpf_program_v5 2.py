# cpf_program4_v2.py
import math
from datetime import datetime
from config_loader_v2 import ConfigLoader
from date_generator_v2 import generate_date_dict
from data_saver_v2 import save_results

def run_simulation(config_path: str = 'config.json', output_format: str = 'pickle'):
    """Run the CPF simulation using the given config, save results in specified format."""
    # Load configuration from JSON
    loader = ConfigLoader(config_path)
    config = loader.data

    # Generate the monthly date dictionary for the simulation timeline
    start_date = config['START_DATE']
    end_date = config['END_DATE']
    date_dict = generate_date_dict(start_date, end_date)
    total_months = len(date_dict)

    # Extract frequently used config values for quick access
    salary_cap = config.get('SALARY_CAP', math.inf)
    salary = config.get('SALARY', 0)
    # Contribution allocation fractions
    alloc_below_55 = config.get('SALARY_ALLOCATION_BELOW_55', {})
    alloc_above_55 = config.get('SALARY_ALLOCATION_ABOVE_55', {})
    sum_alloc_below_55 = sum(alloc_below_55.values())
    sum_alloc_above_55 = sum(alloc_above_55.values())
    # CPF contribution rates by age group (employee + employer)
    contribution_rates = config.get('CPF_CONTRIBUTION_RATES', {})
    # Base interest rates
    OA_rate_below_55 = config.get('OA_INTEREST_RATE_BELOW_55', 0)
    OA_rate_above_55 = config.get('OA_INTEREST_RATE_ABOVE_55', 0)
    SA_rate = config.get('SA_INTEREST_RATE', 0)
    MA_rate = config.get('MA_INTEREST_RATE', 0)
    RA_rate = config.get('RA_INTEREST_RATE', 0)
    # Extra interest rates
    extra_rate_below_55 = config.get('EXTRA_INTEREST_BELOW_55', 0)
    extra_rate_first30_above55 = config.get('EXTRA_INTEREST_FIRST_30K_ABOVE_55', 0)
    extra_rate_next30_above55 = config.get('EXTRA_INTEREST_NEXT_30K_ABOVE_55', 0)
    # Retirement sums and payout configuration
    brs_amount = config.get('BASIC_RETIREMENT_SUM', {}).get('amount', 0)
    frs_amount = config.get('FULL_RETIREMENT_SUM', {}).get('amount', 0)
    ers_amount = config.get('ENHANCED_RETIREMENT_SUM', {}).get('amount', 0)
    cpf_payment_amount = config.get('CPF_PAYMENT_AMOUNT', 0)
    # Decide which retirement sum target to use based on chosen payout
    target_ra_sum = brs_amount
    if math.isclose(cpf_payment_amount, config.get('CPF_PAYOUT_AMOUNT_FRS', -1), rel_tol=1e-9):
        target_ra_sum = frs_amount
    elif math.isclose(cpf_payment_amount, config.get('CPF_PAYOUT_AMOUNT_ERS', -1), rel_tol=1e-9):
        target_ra_sum = ers_amount
    else:
        target_ra_sum = brs_amount  # default to BRS

    # Prepare milestone dates from birth date
    birth_date = config['BIRTH_DATE']
    brs_transfer_date = config.get('AGE_FOR_BRS_TRANSFER_DATE', datetime(birth_date.year+55, birth_date.month, birth_date.day))
    cpf_payout_date = datetime(birth_date.year + config.get('AGE_FOR_CPF_PAYOUT', 67),
                               birth_date.month, birth_date.day)

    # Initialize account balances (could be extended to take initial balances from config if provided)
    OA_balance = SA_balance = MA_balance = RA_balance = 0.0
    brs_transfer_done = False
    payout_started = False

    results = []  # to collect results each month

    for month_idx in range(total_months):
        current_date = date_dict[month_idx]
        # Compute current age in years
        age_years = current_date.year - birth_date.year
        if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
            age_years -= 1

        # **Age 55 event** – Transfer to RA if not done and reaching 55th birthday
        if not brs_transfer_done and current_date >= brs_transfer_date:
            amount_needed = target_ra_sum
            # Transfer from SA then OA to Retirement Account (RA)
            transfer_from_SA = min(SA_balance, amount_needed)
            SA_balance -= transfer_from_SA; amount_needed -= transfer_from_SA
            transfer_from_OA = min(OA_balance, amount_needed)
            OA_balance -= transfer_from_OA; amount_needed -= transfer_from_OA
            RA_balance += (transfer_from_SA + transfer_from_OA)
            brs_transfer_done = True

        # Determine contribution rates bracket by age
        if age_years < 55:
            bracket = 'below_55'; fractions = alloc_below_55; frac_sum = sum_alloc_below_55
        elif age_years < 60:
            bracket = '55_to_60'; fractions = alloc_above_55; frac_sum = sum_alloc_above_55
        elif age_years < 65:
            bracket = '60_to_65'; fractions = alloc_above_55; frac_sum = sum_alloc_above_55
        elif age_years < 70:
            bracket = '65_to_70'; fractions = alloc_above_55; frac_sum = sum_alloc_above_55
        else:
            bracket = 'above_70'; fractions = alloc_above_55; frac_sum = sum_alloc_above_55

        rates = contribution_rates.get(bracket, {"employee": 0.0, "employer": 0.0})
        combined_rate = rates["employee"] + rates["employer"]
        wage_effective = min(salary, salary_cap)  # cap the salary for CPF computation
        total_contribution = combined_rate * wage_effective
        # Allocate contributions to accounts (OA, SA/RA, MA) based on fraction distribution
        if frac_sum == 0:
            contribution_to_accounts = {"oa": 0.0, "sa": 0.0, "ra": 0.0, "ma": 0.0}
        else:
            contribution_to_accounts = {acc: total_contribution * (frac / frac_sum) 
                                        for acc, frac in fractions.items()}
        # Update balances with contributions
        OA_balance += contribution_to_accounts.get("oa", 0.0)
        SA_balance += contribution_to_accounts.get("sa", 0.0)
        MA_balance += contribution_to_accounts.get("ma", 0.0)
        RA_balance += contribution_to_accounts.get("ra", 0.0)

        # Deduct monthly housing loan payment from OA
        m_count = month_idx + 1  # month count (1-indexed for easier year grouping)
        if m_count <= 24:
            loan_payment = config.get('LOAN_PAYMENT_YEAR_1_2', 0.0)
        elif m_count <= 36:
            loan_payment = config.get('LOAN_PAYMENT_YEAR_3', 0.0)
        else:
            loan_payment = config.get('LOAN_PAYMENT_YEAR_4_BEYOND', 0.0)
        if loan_payment:
            if OA_balance >= loan_payment:
                OA_balance -= loan_payment
            else:
                OA_balance = 0.0  # if OA insufficient, assume remainder paid externally (not modeled)

        # Calculate monthly interest for each account
        oa_rate = OA_rate_below_55 if age_years < 55 else OA_rate_above_55
        OA_interest = OA_balance * (oa_rate / 100.0) / 12.0
        SA_interest = SA_balance * (SA_rate / 100.0) / 12.0
        MA_interest = MA_balance * (MA_rate / 100.0) / 12.0
        RA_interest = RA_balance * (RA_rate / 100.0) / 12.0

        # Calculate extra interest (1% on first 60k combined, +1% on first 30k for 55+)
        total_balance = OA_balance + SA_balance + MA_balance + RA_balance
        OA_extra = SA_extra = MA_extra = RA_extra = 0.0
        if age_years < 55:
            # Extra 1% on up to 60k of combined balances (max 20k of OA)
            cap = 60000.0
            allowed_OA = min(OA_balance, 20000.0)
            pool = min(total_balance, cap)
            oa_part = min(allowed_OA, pool); pool -= oa_part
            sa_part = min(SA_balance, pool); pool -= sa_part
            ma_part = min(MA_balance, pool); pool -= ma_part
            # extra interest applied
            OA_extra = oa_part * (extra_rate_below_55/100.0) / 12.0
            SA_extra = sa_part * (extra_rate_below_55/100.0) / 12.0
            MA_extra = ma_part * (extra_rate_below_55/100.0) / 12.0
            RA_extra = 0.0
        else:
            # Extra interest for 55 and above:
            # 1.5% on first 30k (in config), 1.0% on next 30k
            first_band = 30000.0; second_band = 30000.0
            band1_pool = min(total_balance, first_band)
            allowed_OA = min(OA_balance, 20000.0)
            # allocate first 30k across accounts (respect OA cap 20k)
            oa_part1 = min(allowed_OA, band1_pool); band1_pool -= oa_part1
            ra_part1 = min(RA_balance, band1_pool); band1_pool -= ra_part1
            sa_part1 = min(SA_balance, band1_pool); band1_pool -= sa_part1
            ma_part1 = min(MA_balance, band1_pool); band1_pool -= ma_part1
            # allocate next 30k across accounts (OA already capped, exclude OA)
            band2_pool = 0.0
            if total_balance > first_band:
                band2_pool = min(total_balance - first_band, second_band)
            ra_part2 = min(max(RA_balance - ra_part1, 0.0), band2_pool); band2_pool -= ra_part2
            sa_part2 = min(max(SA_balance - sa_part1, 0.0), band2_pool); band2_pool -= sa_part2
            ma_part2 = min(max(MA_balance - ma_part1, 0.0), band2_pool); band2_pool -= ma_part2
            # compute extra interest for each account part
            OA_extra = oa_part1 * (extra_rate_first30_above55/100.0) / 12.0
            RA_extra = (ra_part1 * (extra_rate_first30_above55/100.0) + ra_part2 * (extra_rate_next30_above55/100.0)) / 12.0
            SA_extra = (sa_part1 * (extra_rate_first30_above55/100.0) + sa_part2 * (extra_rate_next30_above55/100.0)) / 12.0
            MA_extra = (ma_part1 * (extra_rate_first30_above55/100.0) + ma_part2 * (extra_rate_next30_above55/100.0)) / 12.0

        # Apply interest to balances
        OA_balance += OA_interest + OA_extra
        SA_balance += SA_interest + SA_extra
        MA_balance += MA_interest + MA_extra
        RA_balance += RA_interest + RA_extra

        # **Age 67 event** – Start CPF retirement payouts from RA
        if not payout_started and current_date >= cpf_payout_date:
            payout_started = True
        if payout_started and cpf_payment_amount > 0:
            # Deduct monthly payout from RA (ensure it doesn't go negative)
            RA_balance = RA_balance - cpf_payment_amount if RA_balance >= cpf_payment_amount else 0.0

        # Record the month’s results
        results.append({
            "month_index": month_idx,
            "date": current_date.strftime("%Y-%m-%d"),
            "age": age_years,
            "OA_balance": round(OA_balance, 2),
            "SA_balance": round(SA_balance, 2),
            "MA_balance": round(MA_balance, 2),
            "RA_balance": round(RA_balance, 2)
        })

    # Save all results at once in the desired format (binary by default for efficiency)
    output_file = f"cpf_simulation_results.{ 'pkl' if output_format.lower()=='pickle' else output_format }"
    save_results(results, output_file, format=output_format)
    return results

if __name__ == "__main__":
    run_simulation()