import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.api.router import api_router
from app.seed.seed_data import seed_database
from app.services.simulation_service import simulation_service
from app.tools.registry import registry  # Registers all tools

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("banking_platform")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan managing startup database verification and clean background task cancellation."""
    logger.info("Initializing Banking AI Platform backend...")
    # Initialize DB tables and seed if empty
    seed_database(force_reset=False)
    logger.info(f"Loaded {len(registry.list_tools())} tools in Tool Registry.")
    yield
    # Shutdown clean up
    logger.info("Shutting down Banking AI Platform backend...")
    simulation_service.stop_simulation()

app = FastAPI(
    title="AI Banking Intelligence & Autonomous Multi-Agent Platform",
    description="Production-inspired MVP for simulated real-time banking operations and multi-agent orchestration.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID and Request Logging Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID") or f"REQ-{uuid.uuid4().hex[:8].upper()}"
    request.state.correlation_id = corr_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = corr_id
    return response

# Root and Health Endpoints
@app.get("/")
def root():
    return {
        "platform": "AI Banking Intelligence & Autonomous Multi-Agent Platform",
        "status": "ONLINE",
        "mode": "SIMULATION_MODE",
        "docs_url": "/docs",
        "disclaimer": "SIMULATION MODE — All customers, accounts, transactions, alerts, and loan assessments are fictional."
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "sqlite_connected",
        "registered_tools": len(registry.list_tools()),
        "is_simulator_running": simulation_service.is_running,
        "llm_provider": settings.LLM_PROVIDER if settings.LLM_API_KEY else "deterministic_fallback"
    }

# Top-level WebSocket for Live Simulator Feed
@app.websocket("/ws/simulator")
async def ws_simulator_root(websocket: WebSocket):
    await simulation_service.connect_client(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        simulation_service.disconnect_client(websocket)
    except Exception:
        simulation_service.disconnect_client(websocket)

# Include API Router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
