from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.services.simulation_service import simulation_service

router = APIRouter(prefix="/simulator", tags=["Real-Time Simulator"])

class GenerateDemoTxRequest(BaseModel):
    force_suspicious: bool = False

@router.get("/status")
def get_simulator_status():
    return {
        "is_running": simulation_service.is_running,
        "interval_seconds": simulation_service.interval_seconds,
        "connected_clients": len(simulation_service.active_connections)
    }

@router.post("/start")
def start_simulator():
    return simulation_service.start_simulation()

@router.post("/stop")
def stop_simulator():
    return simulation_service.stop_simulation()

@router.post("/generate")
async def generate_transaction(req: GenerateDemoTxRequest | None = None):
    force_suspicious = req.force_suspicious if req else False
    tx = await simulation_service.generate_single_transaction(force_suspicious=force_suspicious)
    return {"message": "Demo transaction generated", "transaction": tx}

@router.websocket("/ws")
async def simulator_websocket_endpoint(websocket: WebSocket):
    await simulation_service.connect_client(websocket)
    try:
        while True:
            # Keep connection open and receive potential client heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        simulation_service.disconnect_client(websocket)
    except Exception:
        simulation_service.disconnect_client(websocket)
