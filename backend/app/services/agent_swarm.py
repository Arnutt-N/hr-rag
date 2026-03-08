"""
Agent Swarm System - Multi-agent collaborative system
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from app.services.llm.langchain_service import get_llm_service


class AgentRole(Enum):
    """Agent roles in swarm."""
    COORDINATOR = "coordinator"      # ประสานงาน
    RESEARCHER = "researcher"        # ค้นคว้า
    WRITER = "writer"                # เขียน
    CRITIC = "critic"                # ตรวจสอบ
    EXECUTOR = "executor"            # ดำเนินการ
    SPECIALIST = "specialist"        # ผู้เชี่ยวชาญ


class AgentStatus(Enum):
    """Agent status."""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    DONE = "done"


@dataclass
class AgentMessage:
    """Message between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""  # "broadcast" for all
    message_type: str = "task"  # task, result, query, broadcast
    content: Any = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmAgent:
    """Agent in swarm."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: AgentRole = AgentRole.SPECIALIST
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    llm_provider: str = "openai"
    system_prompt: str = ""
    memory: List[Dict] = field(default_factory=list)
    task_count: int = 0
    success_count: int = 0
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process assigned task."""
        self.status = AgentStatus.WORKING
        self.task_count += 1
        
        try:
            # Get LLM service
            llm = get_llm_service(self.llm_provider)
            
            # Build prompt
            prompt = self._build_task_prompt(task)
            
            # Process
            response = await llm.chat([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            # Store in memory
            self.memory.append({
                "task": task,
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.status = AgentStatus.DONE
            self.success_count += 1
            
            return {
                "success": True,
                "agent_id": self.id,
                "agent_name": self.name,
                "result": response,
                "role": self.role.value
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            return {
                "success": False,
                "agent_id": self.id,
                "error": str(e)
            }
    
    def _build_task_prompt(self, task: Dict[str, Any]) -> str:
        """Build task prompt."""
        return f"""หน้าที่: {self.role.value}
ชื่อ: {self.name}

งานที่ได้รับ:
{json.dumps(task, ensure_ascii=False, indent=2)}

ความสามารถ: {', '.join(self.capabilities)}

ดำเนินการตามหน้าที่ของคุณ:"""


class AgentSwarm:
    """
    Agent Swarm - Multi-agent collaborative system.
    
    Features:
    - Dynamic agent creation
    - Task distribution
    - Inter-agent communication
    - Result aggregation
    """
    
    def __init__(self, name: str = "swarm"):
        """Initialize swarm."""
        self.name = name
        self.swarm_id = str(uuid.uuid4())
        self.agents: Dict[str, SwarmAgent] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.results: List[Dict] = []
        self.running = False
        self.coordinator: Optional[SwarmAgent] = None
    
    def create_agent(
        self,
        name: str,
        role: AgentRole,
        capabilities: List[str],
        llm_provider: str = "openai",
        system_prompt: Optional[str] = None
    ) -> SwarmAgent:
        """Create new agent in swarm."""
        
        # Default prompts by role
        default_prompts = {
            AgentRole.COORDINATOR: "คุณเป็นผู้ประสานงานหลัก จัดการและ分配งานให้กับทีม",
            AgentRole.RESEARCHER: "คุณเป็นผู้ค้นคว้า หาข้อมูลและวิเคราะห์",
            AgentRole.WRITER: "คุณเป็นนักเขียน สร้างเนื้อหาที่มีคุณภาพ",
            AgentRole.CRITIC: "คุณเป็นผู้ตรวจสอบ ตรวจหาข้อผิดพลาดและแนะนำ",
            AgentRole.EXECUTOR: "คุณเป็นผู้ดำเนินการ ลงมือทำตามแผน",
            AgentRole.SPECIALIST: "คุณเป็นผู้เชี่ยวชาญ ให้คำปรึกษาเฉพาะทาง"
        }
        
        agent = SwarmAgent(
            name=name,
            role=role,
            capabilities=capabilities,
            llm_provider=llm_provider,
            system_prompt=system_prompt or default_prompts.get(role, "คุณเป็นสมาชิกทีม")
        )
        
        self.agents[agent.id] = agent
        
        # Set first coordinator
        if role == AgentRole.COORDINATOR and not self.coordinator:
            self.coordinator = agent
        
        return agent
    
    async def broadcast(self, message: AgentMessage):
        """Broadcast message to all agents."""
        for agent in self.agents.values():
            if agent.id != message.sender:
                await self.message_queue.put(message)
    
    async def send_to_agent(self, agent_id: str, message: AgentMessage):
        """Send message to specific agent."""
        if agent_id in self.agents:
            await self.message_queue.put(message)
    
    async def execute_task(
        self,
        task: Dict[str, Any],
        strategy: str = "parallel"  # parallel, sequential, specialist
    ) -> Dict[str, Any]:
        """
        Execute task with swarm.
        
        Args:
            task: Task definition
            strategy: Execution strategy
        
        Returns:
            Combined results
        """
        self.running = True
        
        if strategy == "parallel":
            return await self._execute_parallel(task)
        elif strategy == "sequential":
            return await self._execute_sequential(task)
        elif strategy == "specialist":
            return await self._execute_specialist(task)
        else:
            return await self._execute_parallel(task)
    
    async def _execute_parallel(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with all agents in parallel."""
        # Create subtasks for each agent
        subtasks = []
        for agent in self.agents.values():
            if agent.role != AgentRole.COORDINATOR:
                subtask = {
                    **task,
                    "agent_role": agent.role.value,
                    "agent_capabilities": agent.capabilities
                }
                subtasks.append((agent, subtask))
        
        # Execute all in parallel
        tasks = [agent.process(subtask) for agent, subtask in subtasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        # Coordinator synthesizes final result
        if self.coordinator and successful:
            final_result = await self._synthesize_results(task, successful)
        else:
            final_result = self._simple_aggregate(successful)
        
        return {
            "success": len(failed) == 0,
            "swarm_id": self.swarm_id,
            "strategy": "parallel",
            "total_agents": len(subtasks),
            "successful": len(successful),
            "failed": len(failed),
            "individual_results": results,
            "final_result": final_result
        }
    
    async def _execute_sequential(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents in sequence."""
        results = []
        context = task.copy()
        
        # Order: Researcher -> Writer -> Critic -> Executor
        role_order = [
            AgentRole.RESEARCHER,
            AgentRole.WRITER,
            AgentRole.CRITIC,
            AgentRole.EXECUTOR
        ]
        
        for role in role_order:
            agents = [a for a in self.agents.values() if a.role == role]
            for agent in agents:
                subtask = {**context, "previous_results": results}
                result = await agent.process(subtask)
                results.append(result)
                
                if result.get("success"):
                    context["last_output"] = result.get("result")
        
        return {
            "success": True,
            "swarm_id": self.swarm_id,
            "strategy": "sequential",
            "steps": len(results),
            "results": results,
            "final_output": context.get("last_output")
        }
    
    async def _execute_specialist(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with best matching specialist."""
        # Find best matching agent by capabilities
        task_requirements = task.get("requirements", [])
        best_agent = None
        best_score = 0
        
        for agent in self.agents.values():
            score = sum(1 for req in task_requirements if req in agent.capabilities)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if not best_agent:
            best_agent = list(self.agents.values())[0] if self.agents else None
        
        if best_agent:
            result = await best_agent.process(task)
            return {
                "success": result.get("success"),
                "swarm_id": self.swarm_id,
                "strategy": "specialist",
                "selected_agent": best_agent.name,
                "agent_role": best_agent.role.value,
                "result": result
            }
        
        return {"success": False, "error": "No agents available"}
    
    async def _synthesize_results(
        self,
        original_task: Dict[str, Any],
        results: List[Dict]
    ) -> str:
        """Have coordinator synthesize final result."""
        if not self.coordinator:
            return self._simple_aggregate(results)
        
        synthesis_prompt = f"""รวบรวมผลลัพธ์จากทีมให้เป็นคำตอบสมบูรณ์:

งานต้นฉบับ:
{json.dumps(original_task, ensure_ascii=False)}

ผลลัพธ์จากสมาชิกทีม:
{chr(10).join([f"- {r.get('agent_name')} ({r.get('role')}): {r.get('result', '')[:200]}" for r in results])}

รวบรวมเป็นคำตอบขั้นสุดท้าย:"""
        
        llm = get_llm_service(self.coordinator.llm_provider)
        final = await llm.chat([{"role": "user", "content": synthesis_prompt}])
        
        return final
    
    def _simple_aggregate(self, results: List[Dict]) -> str:
        """Simple aggregation without coordinator."""
        outputs = [r.get("result", "") for r in results if r.get("success")]
        return "\n\n".join(outputs)
    
    def get_status(self) -> Dict[str, Any]:
        """Get swarm status."""
        return {
            "swarm_id": self.swarm_id,
            "name": self.name,
            "total_agents": len(self.agents),
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role.value,
                    "status": a.status.value,
                    "tasks": a.task_count,
                    "success_rate": round(a.success_count / a.task_count * 100, 1) if a.task_count > 0 else 0
                }
                for a in self.agents.values()
            ],
            "coordinator": self.coordinator.name if self.coordinator else None
        }
    
    def reset(self):
        """Reset all agents."""
        for agent in self.agents.values():
            agent.status = AgentStatus.IDLE
            agent.memory = []
        self.results = []


# Factory functions
def create_research_swarm() -> AgentSwarm:
    """Create research-focused swarm."""
    swarm = AgentSwarm("research_team")
    
    swarm.create_agent(
        name="ผู้ประสานงาน",
        role=AgentRole.COORDINATOR,
        capabilities=["planning", "coordination", "synthesis"]
    )
    
    swarm.create_agent(
        name="นักค้นคว้า 1",
        role=AgentRole.RESEARCHER,
        capabilities=["research", "analysis", "data_collection"]
    )
    
    swarm.create_agent(
        name="นักค้นคว้า 2",
        role=AgentRole.RESEARCHER,
        capabilities=["research", "fact_checking", "sources"]
    )
    
    swarm.create_agent(
        name="นักเขียน",
        role=AgentRole.WRITER,
        capabilities=["writing", "editing", "formatting"]
    )
    
    swarm.create_agent(
        name="ผู้ตรวจสอบ",
        role=AgentRole.CRITIC,
        capabilities=["review", "quality_check", "feedback"]
    )
    
    return swarm


def create_content_swarm() -> AgentSwarm:
    """Create content creation swarm."""
    swarm = AgentSwarm("content_team")
    
    swarm.create_agent(
        name="หัวหน้าทีม",
        role=AgentRole.COORDINATOR,
        capabilities=["planning", "strategy"]
    )
    
    swarm.create_agent(
        name="นักเขียนเนื้อหา",
        role=AgentRole.WRITER,
        capabilities=["content_writing", "copywriting", "seo"]
    )
    
    swarm.create_agent(
        name="นักออกแบบ",
        role=AgentRole.SPECIALIST,
        capabilities=["design", "visual", "layout"]
    )
    
    swarm.create_agent(
        name="ผู้ตรวจสอบคุณภาพ",
        role=AgentRole.CRITIC,
        capabilities=["review", "proofreading", "quality"]
    )
    
    return swarm
