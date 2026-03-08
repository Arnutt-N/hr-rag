"""
Agent Swarm API Router - Native FastAPI endpoints for agent swarm
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.services.agent_swarm import (
    AgentSwarm, AgentRole,
    create_research_swarm, create_content_swarm
)

router = APIRouter(prefix="/swarm", tags=["Agent Swarm"])


# Models
class CreateSwarmRequest(BaseModel):
    name: str


class AddAgentRequest(BaseModel):
    name: str
    role: str  # coordinator, researcher, writer, critic, executor, specialist
    capabilities: List[str]
    llm_provider: str = "openai"


class ExecuteTaskRequest(BaseModel):
    task: dict
    strategy: str = "parallel"  # parallel, sequential, specialist


class SwarmResponse(BaseModel):
    swarm_id: str
    name: str
    total_agents: int
    status: str


# In-memory storage (use Redis/DB in production)
_active_swarms: dict = {}


@router.post("/create", response_model=SwarmResponse)
async def create_swarm(request: CreateSwarmRequest):
    """
    สร้าง Agent Swarm ใหม่
    
    Create new agent swarm.
    """
    try:
        swarm = AgentSwarm(name=request.name)
        _active_swarms[swarm.swarm_id] = swarm
        
        return SwarmResponse(
            swarm_id=swarm.swarm_id,
            name=swarm.name,
            total_agents=0,
            status="created"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{swarm_id}/agents")
async def add_agent(swarm_id: str, request: AddAgentRequest):
    """
    เพิ่ม Agent เข้า Swarm
    
    Add agent to swarm.
    """
    if swarm_id not in _active_swarms:
        raise HTTPException(status_code=404, detail="Swarm not found")
    
    swarm = _active_swarms[swarm_id]
    
    role_map = {
        "coordinator": AgentRole.COORDINATOR,
        "researcher": AgentRole.RESEARCHER,
        "writer": AgentRole.WRITER,
        "critic": AgentRole.CRITIC,
        "executor": AgentRole.EXECUTOR,
        "specialist": AgentRole.SPECIALIST
    }
    
    try:
        agent = swarm.create_agent(
            name=request.name,
            role=role_map.get(request.role, AgentRole.SPECIALIST),
            capabilities=request.capabilities,
            llm_provider=request.llm_provider
        )
        
        return {
            "success": True,
            "agent_id": agent.id,
            "agent_name": agent.name,
            "role": agent.role.value,
            "swarm_id": swarm_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{swarm_id}/execute")
async def execute_task(swarm_id: str, request: ExecuteTaskRequest):
    """
    สั่งให้ Swarm ทำงาน
    
    Execute task with swarm.
    """
    if swarm_id not in _active_swarms:
        raise HTTPException(status_code=404, detail="Swarm not found")
    
    swarm = _active_swarms[swarm_id]
    
    try:
        result = await swarm.execute_task(
            task=request.task,
            strategy=request.strategy
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{swarm_id}/status")
async def get_swarm_status(swarm_id: str):
    """
    ดูสถานะ Swarm
    
    Get swarm status.
    """
    if swarm_id not in _active_swarms:
        raise HTTPException(status_code=404, detail="Swarm not found")
    
    swarm = _active_swarms[swarm_id]
    return swarm.get_status()


@router.post("/presets/{preset_type}")
async def create_preset_swarm(preset_type: str):
    """
    สร้าง Swarm จาก Preset
    
    Create swarm from preset.
    
    - research_team: ทีมวิจัย 5 คน
    - content_team: ทีมสร้างเนื้อหา 4 คน
    """
    try:
        if preset_type == "research_team":
            swarm = create_research_swarm()
        elif preset_type == "content_team":
            swarm = create_content_swarm()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown preset: {preset_type}")
        
        _active_swarms[swarm.swarm_id] = swarm
        
        return {
            "success": True,
            "swarm_id": swarm.swarm_id,
            "name": swarm.name,
            "preset": preset_type,
            "total_agents": len(swarm.agents),
            "agents": [
                {"name": a.name, "role": a.role.value}
                for a in swarm.agents.values()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_swarms():
    """
    แสดงรายการ Swarms ทั้งหมด
    
    List all active swarms.
    """
    return {
        "total": len(_active_swarms),
        "swarms": [
            {
                "swarm_id": sid,
                "name": s.name,
                "total_agents": len(s.agents)
            }
            for sid, s in _active_swarms.items()
        ]
    }


@router.delete("/{swarm_id}")
async def delete_swarm(swarm_id: str):
    """
    ลบ Swarm
    
    Delete swarm.
    """
    if swarm_id not in _active_swarms:
        raise HTTPException(status_code=404, detail="Swarm not found")
    
    del _active_swarms[swarm_id]
    return {"success": True, "message": f"Swarm {swarm_id} deleted"}
