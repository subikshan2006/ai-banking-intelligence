from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.loan import LoanApplication
from app.schemas.loans import (
    LoanEvaluateRequest, LoanEvaluateResponse,
    LoanCompareRequest, LoanCompareResponse,
    LoanScenarioInput
)
from app.tools.loan_tools import evaluate_loan_eligibility, compare_loan_scenarios, calculate_monthly_emi

router = APIRouter(prefix="/loans", tags=["Loans & Credit"])

@router.get("")
def list_loan_applications(
    customer_id: str | None = None,
    approval_status: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(LoanApplication)
    if customer_id:
        query = query.filter(LoanApplication.customer_id == customer_id.upper())
    if approval_status:
        query = query.filter(LoanApplication.approval_status == approval_status.upper())

    loans = query.order_by(LoanApplication.created_at.desc()).all()
    return [
        {
            "id": l.id,
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

@router.get("/{application_id}")
def get_loan_details(application_id: str, db: Session = Depends(get_db)):
    loan = db.query(LoanApplication).filter(LoanApplication.id == application_id.upper()).first()
    if not loan:
        raise HTTPException(status_code=404, detail=f"Loan application '{application_id}' not found.")
    return {
        "id": loan.id,
        "customer_id": loan.customer_id,
        "requested_amount": loan.requested_amount,
        "tenure_months": loan.tenure_months,
        "purpose": loan.purpose,
        "interest_rate": loan.interest_rate,
        "estimated_emi": loan.estimated_emi,
        "dti_ratio": loan.dti_ratio,
        "assessment_result": loan.assessment_result,
        "approval_status": loan.approval_status,
        "assessment_notes": loan.assessment_notes,
        "created_at": loan.created_at.isoformat()
    }

@router.post("/evaluate", response_model=LoanEvaluateResponse)
def evaluate_loan_endpoint(req: LoanEvaluateRequest, db: Session = Depends(get_db)):
    try:
        res = evaluate_loan_eligibility(
            db=db,
            customer_id=req.customer_id,
            requested_amount=req.requested_amount,
            tenure_months=req.tenure_months,
            purpose=req.purpose
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/compare", response_model=LoanCompareResponse)
def compare_loans_endpoint(req: LoanCompareRequest, db: Session = Depends(get_db)):
    try:
        scenarios_dicts = [s.model_dump() for s in req.scenarios]
        return compare_loan_scenarios(db=db, scenarios=scenarios_dicts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate-emi")
def calculate_emi_endpoint(input_data: LoanScenarioInput, db: Session = Depends(get_db)):
    return calculate_monthly_emi(
        db=db,
        principal=input_data.principal,
        annual_interest_rate=input_data.interest_rate,
        tenure_months=input_data.tenure_months
    )
