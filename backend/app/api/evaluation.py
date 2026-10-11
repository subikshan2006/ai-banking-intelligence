from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.evaluation import EvaluationResponse
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Observability"])

@router.get("/runs")
def list_evaluation_runs(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    return evaluation_service.get_runs(db, limit=limit)

@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation_suite(db: Session = Depends(get_db)):
    """Trigger the benchmark evaluation suite measuring intent accuracy and groundedness."""
    return await evaluation_service.run_suite(db)
