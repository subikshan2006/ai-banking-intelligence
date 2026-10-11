from typing import Literal
from pydantic import BaseModel, Field

class LoanScenarioInput(BaseModel):
    principal: float = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0)
    interest_rate: float = Field(..., ge=0)

class LoanScenarioOutput(BaseModel):
    scenario_id: str
    principal: float
    tenure_months: int
    interest_rate: float
    monthly_emi: float
    total_repayment: float
    total_interest: float

class LoanEvaluateRequest(BaseModel):
    customer_id: str
    requested_amount: float = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0)
    purpose: str = "Personal"

class LoanEvaluateResponse(BaseModel):
    customer_id: str
    requested_amount: float
    tenure_months: int
    interest_rate: float
    monthly_emi: float
    monthly_income: float
    existing_monthly_debt: float
    projected_total_monthly_debt: float
    debt_to_income_ratio: float
    assessment_result: Literal["ELIGIBLE", "HIGH_RISK_DTI", "REQUIRES_MANUAL_REVIEW", "INELIGIBLE"]
    positive_factors: list[str] = Field(default_factory=list)
    caution_factors: list[str] = Field(default_factory=list)
    disclaimer: str = "Experimental simulation only. This is not a credit bureau result, financial recommendation, or actual loan approval."

class LoanCompareRequest(BaseModel):
    scenarios: list[LoanScenarioInput]

class LoanCompareResponse(BaseModel):
    scenarios: list[LoanScenarioOutput]
    comparison_summary: str
