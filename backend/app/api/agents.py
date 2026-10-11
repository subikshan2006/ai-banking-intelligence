from fastapi import APIRouter
from app.agents.supervisor import supervisor
from app.tools.registry import registry

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("/status")
def get_agents_status():
    agents_info = []
    for name, agent in supervisor.agents_map.items():
        agents_info.append({
            "name": name,
            "description": agent.description,
            "status": "ONLINE",
            "type": "Specialized Banking Agent"
        })
    agents_info.append({
        "name": "SupervisorAgent",
        "description": "Central orchestrator coordinating agent selection, DAG task planning, and answer grounding.",
        "status": "ONLINE",
        "type": "Orchestrator"
    })
    return {
        "total_agents": len(agents_info),
        "agents": agents_info
    }

@router.get("/tools")
def list_registered_tools():
    return {
        "total_tools": len(registry.list_tools()),
        "tools": registry.list_tools()
    }
