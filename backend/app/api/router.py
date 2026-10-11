from fastapi import APIRouter
from app.api.dashboard import router as dashboard_router
from app.api.customers import router as customers_router
from app.api.transactions import router as transactions_router
from app.api.fraud import router as fraud_router
from app.api.loans import router as loans_router
from app.api.assistant import router as assistant_router
from app.api.agents import router as agents_router
from app.api.approvals import router as approvals_router
from app.api.investigations import router as investigations_router
from app.api.knowledge import router as knowledge_router
from app.api.simulator import router as simulator_router
from app.api.audit import router as audit_router
from app.api.notifications import router as notifications_router
from app.api.evaluation import router as evaluation_router

api_router = APIRouter(prefix="/api")

api_router.include_router(dashboard_router)
api_router.include_router(customers_router)
api_router.include_router(transactions_router)
api_router.include_router(fraud_router)
api_router.include_router(loans_router)
api_router.include_router(assistant_router)
api_router.include_router(agents_router)
api_router.include_router(approvals_router)
api_router.include_router(investigations_router)
api_router.include_router(knowledge_router)
api_router.include_router(simulator_router)
api_router.include_router(audit_router)
api_router.include_router(notifications_router)
api_router.include_router(evaluation_router)
