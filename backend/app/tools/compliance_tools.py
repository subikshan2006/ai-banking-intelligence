from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.registry import registry
from app.models.customer import Customer
from app.models.policy import PolicyDocument

class KycArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID, e.g. CUST1004")

@registry.register(
    name="get_kyc_status",
    description="Retrieve the current simulated KYC and Customer Due Diligence status of a customer.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=KycArgs
)
def get_kyc_status(db: Session, customer_id: str) -> dict[str, Any]:
    cust = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
    if not cust:
        raise ValueError(f"Customer '{customer_id}' not found.")
    
    docs_status = {
        "government_id": "VERIFIED" if cust.kyc_status == "VERIFIED" else "PENDING_UPLOAD",
        "address_proof": "VERIFIED" if cust.kyc_status == "VERIFIED" else "PENDING_UPLOAD",
        "pan_tax_id": "VERIFIED" if cust.kyc_status != "REJECTED" else "INVALID_OR_MISMATCH",
        "biometric_verification": "COMPLETED" if cust.kyc_status == "VERIFIED" else "NOT_INITIATED"
    }

    return {
        "customer_id": cust.id,
        "name": cust.name,
        "kyc_status": cust.kyc_status,
        "risk_rating": cust.risk_rating,
        "documents": docs_status,
        "compliance_notes": f"Customer holds {cust.kyc_status} KYC status under CDD guidelines."
    }

class ComplianceCheckArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    context: str = Field(default="retail_lending", description="Context of review, e.g. retail_lending or account_monitoring")

@registry.register(
    name="evaluate_compliance",
    description="Evaluate customer profile against simulated regulatory guidelines, loan policies, and AML checklists.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=ComplianceCheckArgs
)
def evaluate_compliance(db: Session, customer_id: str, context: str = "retail_lending") -> dict[str, Any]:
    cust = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
    if not cust:
        raise ValueError(f"Customer '{customer_id}' not found.")

    findings = []
    status = "COMPLIANT"

    if cust.kyc_status != "VERIFIED":
        findings.append(f"KYC status is {cust.kyc_status}. Policy POL-003 requires verified identity for credit facilities.")
        status = "NON_COMPLIANT_KYC"
    
    if cust.risk_rating == "HIGH":
        findings.append("High risk internal AML rating. Enhanced Due Diligence (EDD) required under POL-002.")
        if status == "COMPLIANT":
            status = "REQUIRES_ENHANCED_DUE_DILIGENCE"

    if not findings:
        findings.append("No active compliance red flags identified. Customer meets baseline due diligence criteria.")

    return {
        "customer_id": cust.id,
        "compliance_verdict": status,
        "findings": findings,
        "referenced_policies": ["POL-002", "POL-003"],
        "disclaimer": "Simulated regulatory compliance check for demonstration purposes."
    }
