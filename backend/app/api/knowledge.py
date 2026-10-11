import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.policy import PolicyDocument
from app.services.knowledge_service import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge & RAG"])

@router.get("/search")
def search_knowledge_endpoint(query: str = Query(..., min_length=2), top_k: int = 3, db: Session = Depends(get_db)):
    return knowledge_service.search_policies(db, query, top_k=top_k)

@router.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    docs = db.query(PolicyDocument).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "version": d.version,
            "effective_date": d.effective_date,
            "passages_count": len(json.loads(d.passages)) if d.passages else 0
        }
        for d in docs
    ]

@router.get("/policies/{policy_id}")
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    doc = db.query(PolicyDocument).filter(PolicyDocument.id == policy_id.upper()).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found.")
    return {
        "id": doc.id,
        "title": doc.title,
        "category": doc.category,
        "version": doc.version,
        "effective_date": doc.effective_date,
        "content": doc.content,
        "passages": json.loads(doc.passages) if doc.passages else []
    }
