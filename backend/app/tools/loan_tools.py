from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.registry import registry
from app.models.customer import Customer
from app.models.loan import LoanApplication

def compute_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if tenure_months <= 0:
        raise ValueError("Tenure in months must be greater than 0.")
    if principal <= 0:
        raise ValueError("Principal amount must be greater than 0.")
    if annual_rate == 0:
        return round(principal / tenure_months, 2)
    
    monthly_r = (annual_rate / 100.0) / 12.0
    factor = (1 + monthly_r) ** tenure_months
    emi = principal * monthly_r * factor / (factor - 1)
    return round(emi, 2)

class CalcEmiArgs(BaseModel):
    principal: float = Field(..., gt=0, description="Principal loan amount in INR")
    annual_interest_rate: float = Field(..., ge=0, description="Annual interest rate in percentage, e.g. 10.5")
    tenure_months: int = Field(..., gt=0, description="Tenure in months, e.g. 36")

@registry.register(
    name="calculate_monthly_emi",
    description="Calculate exact monthly EMI, total interest, and total repayment using standard amortization mathematics.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=CalcEmiArgs
)
def calculate_monthly_emi(db: Session, principal: float, annual_interest_rate: float, tenure_months: int) -> dict[str, Any]:
    emi = compute_emi(principal, annual_interest_rate, tenure_months)
    total_repayment = round(emi * tenure_months, 2)
    total_interest = round(total_repayment - principal, 2)
    return {
        "principal": principal,
        "annual_interest_rate": annual_interest_rate,
        "tenure_months": tenure_months,
        "monthly_emi": emi,
        "total_interest": total_interest,
        "total_repayment": total_repayment
    }

class EvaluateLoanArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID, e.g. CUST1001")
    requested_amount: float = Field(..., gt=0, description="Requested principal amount in INR")
    tenure_months: int = Field(default=36, gt=0, description="Loan tenure in months")
    purpose: str = Field(default="Personal", description="Purpose of loan")

@registry.register(
    name="evaluate_loan_eligibility",
    description="Evaluate loan eligibility using customer income, existing debts, calculated EMI, and DTI ratio benchmarks.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=EvaluateLoanArgs
)
def evaluate_loan_eligibility(
    db: Session,
    customer_id: str,
    requested_amount: float,
    tenure_months: int = 36,
    purpose: str = "Personal"
) -> dict[str, Any]:
    customer = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
    if not customer:
        raise ValueError(f"Customer '{customer_id}' not found.")

    interest_rate = 10.5  # Standard benchmark prime rate
    emi = compute_emi(requested_amount, interest_rate, tenure_months)
    
    monthly_income = customer.monthly_income
    existing_debt = customer.existing_monthly_debt
    projected_total_debt = existing_debt + emi
    
    dti_ratio = round((projected_total_debt / max(1.0, monthly_income)) * 100.0, 1)

    positive_factors = []
    caution_factors = []

    if customer.kyc_status == "VERIFIED":
        positive_factors.append("Customer KYC status is fully VERIFIED.")
    else:
        caution_factors.append(f"Customer KYC status is {customer.kyc_status} (Verification required prior to disbursement).")

    if monthly_income >= 80000.0:
        positive_factors.append(f"Strong monthly income base of ₹{monthly_income:,.2f}.")
    elif monthly_income < 40000.0:
        caution_factors.append(f"Modest monthly income of ₹{monthly_income:,.2f}.")

    if dti_ratio <= 40.0:
        positive_factors.append(f"Healthy Debt-to-Income (DTI) ratio of {dti_ratio}% (Policy threshold: <40%).")
        assessment_result = "ELIGIBLE"
    elif dti_ratio <= 50.0:
        caution_factors.append(f"Elevated DTI of {dti_ratio}% (Between 40% and 50% - requires secondary verification).")
        assessment_result = "REQUIRES_MANUAL_REVIEW"
    else:
        caution_factors.append(f"High-Risk DTI of {dti_ratio}% exceeds policy prudential ceiling of 50%.")
        assessment_result = "HIGH_RISK_DTI"

    if customer.risk_rating == "HIGH":
        caution_factors.append("Customer profile currently flagged with HIGH internal risk rating.")

    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "requested_amount": requested_amount,
        "tenure_months": tenure_months,
        "interest_rate": interest_rate,
        "monthly_emi": emi,
        "estimated_emi": emi,
        "monthly_income": monthly_income,
        "existing_monthly_debt": existing_debt,
        "projected_total_monthly_debt": round(projected_total_debt, 2),
        "debt_to_income_ratio": dti_ratio,
        "assessment_result": assessment_result,
        "positive_factors": positive_factors,
        "caution_factors": caution_factors,
        "disclaimer": "Experimental simulation only. This is not a credit bureau result, financial recommendation, or actual loan approval."
    }

class CompareScenariosArgs(BaseModel):
    scenarios: list[dict[str, Any]] = Field(..., description="List of scenario dicts with principal, tenure_months, interest_rate")

@registry.register(
    name="compare_loan_scenarios",
    description="Compare multiple loan configurations across EMI, total interest, and cumulative payout.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=CompareScenariosArgs
)
def compare_loan_scenarios(db: Session, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    outputs = []
    for idx, sc in enumerate(scenarios):
        p = float(sc.get("principal", 100000.0))
        t = int(sc.get("tenure_months", 24))
        r = float(sc.get("interest_rate", 10.5))
        emi = compute_emi(p, r, t)
        tot = round(emi * t, 2)
        outputs.append({
            "scenario_id": f"Scenario-{idx+1}",
            "principal": p,
            "tenure_months": t,
            "interest_rate": r,
            "monthly_emi": emi,
            "total_repayment": tot,
            "total_interest": round(tot - p, 2)
        })

    summary_text = f"Analyzed {len(outputs)} loan scenarios. "
    if len(outputs) >= 2:
        diff_emi = abs(outputs[0]["monthly_emi"] - outputs[1]["monthly_emi"])
        summary_text += f"EMI delta between Option 1 and Option 2 is ₹{diff_emi:,.2f}/month."

    return {
        "scenarios": outputs,
        "comparison_summary": summary_text
    }

class GetPendingLoansArgs(BaseModel):
    customer_id: str | None = Field(default=None, description="Optional customer ID filter")

@registry.register(
    name="get_loan_applications",
    description="Retrieve pending and processed simulated loan applications.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=GetPendingLoansArgs
)
def get_loan_applications(db: Session, customer_id: str | None = None) -> list[dict[str, Any]]:
    query = db.query(LoanApplication)
    if customer_id:
        query = query.filter(LoanApplication.customer_id == customer_id.upper())
    loans = query.order_by(LoanApplication.created_at.desc()).all()

    return [
        {
            "application_id": l.id,
            "customer_id": l.customer_id,
            "requested_amount": l.requested_amount,
            "tenure_months": l.tenure_months,
            "purpose": l.purpose,
            "interest_rate": l.interest_rate,
            "estimated_emi": l.estimated_emi,
            "dti_ratio": l.dti_ratio,
            "assessment_result": l.assessment_result,
            "approval_status": l.approval_status,
            "assessment_notes": l.assessment_notes,
            "created_at": l.created_at.isoformat()
        }
        for l in loans
    ]
