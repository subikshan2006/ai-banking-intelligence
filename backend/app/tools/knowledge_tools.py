from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.registry import registry
from app.services.knowledge_service import knowledge_service
from app.models.policy import PolicyDocument

class SearchPolicyArgs(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language search query regarding banking policy")
    top_k: int = Field(default=3, ge=1, le=5)

@registry.register(
    name="search_banking_policies",
    description="Retrieve relevant policy passages and compliance guidelines using local TF-IDF RAG search.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=SearchPolicyArgs
)
def search_banking_policies(db: Session, query: str, top_k: int = 3) -> dict[str, Any]:
    return knowledge_service.search_policies(db, query, top_k=top_k)

class GetPolicyDetailsArgs(BaseModel):
    policy_id: str = Field(..., description="Document ID e.g. POL-001")

@registry.register(
    name="get_policy_details",
    description="Retrieve complete policy text, version history, and full content by document ID.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=GetPolicyDetailsArgs
)
def get_policy_details(db: Session, policy_id: str) -> dict[str, Any]:
    doc = db.query(PolicyDocument).filter(PolicyDocument.id == policy_id.upper()).first()
    if not doc:
        raise ValueError(f"Policy document '{policy_id}' not found.")
    return {
        "document_id": doc.id,
        "title": doc.title,
        "category": doc.category,
        "version": doc.version,
        "effective_date": doc.effective_date,
        "content": doc.content
    }
