"""
Skills API Router - Native FastAPI endpoints for skill management
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.skill_manager import get_skill_registry

router = APIRouter(prefix="/skills", tags=["Skills"])


# Models
class CreateSkillRequest(BaseModel):
    name: str
    description: str
    author: str
    template: str = "basic"  # basic, api, mcp, agent
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class UseSkillRequest(BaseModel):
    skill_id: str
    function_name: str = "main"
    parameters: Optional[dict] = None


class ImportSkillRequest(BaseModel):
    skill_path: str


@router.post("/create")
async def skill_create(request: CreateSkillRequest):
    """
    สร้าง Skill ใหม่จาก Template
    
    Create new skill from template.
    
    - name: ชื่อ Skill
    - description: คำอธิบาย
    - author: ผู้สร้าง
    - template: ประเภท (basic, api, mcp, agent)
    - tags: แท็ก
    - dependencies: Dependencies
    """
    try:
        registry = get_skill_registry()
        skill_path = registry.create_skill(
            name=request.name,
            description=request.description,
            author=request.author,
            template=request.template,
            tags=request.tags or [],
            dependencies=request.dependencies or []
        )
        
        return {
            "success": True,
            "message": f"สร้าง Skill '{request.name}' สำเร็จ",
            "skill_path": skill_path,
            "template": request.template
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def skill_import(request: ImportSkillRequest):
    """
    Import Skill จาก Path
    
    Import skill from directory.
    
    - skill_path: พาธไปยังโฟลเดอร์ Skill
    """
    try:
        registry = get_skill_registry()
        skill = registry.import_skill(request.skill_path)
        
        return {
            "success": True,
            "message": f"Import Skill '{skill.metadata.name}' สำเร็จ",
            "skill_id": skill.metadata.name.lower().replace(" ", "_"),
            "functions": list(skill.functions.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/use")
async def skill_use(request: UseSkillRequest):
    """
    ใช้งาน Skill
    
    Execute skill function.
    
    - skill_id: ID ของ Skill
    - function_name: ชื่อฟังก์ชัน (default: main)
    - parameters: พารามิเตอร์
    """
    try:
        registry = get_skill_registry()
        result = registry.use_skill(
            skill_id=request.skill_id,
            function_name=request.function_name,
            **(request.parameters or {})
        )
        
        return {
            "success": True,
            "skill_id": request.skill_id,
            "function": request.function_name,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def skill_list():
    """
    แสดงรายการ Skills ทั้งหมด
    
    List all registered skills.
    """
    try:
        registry = get_skill_registry()
        skills = registry.list_skills()
        
        return {
            "success": True,
            "total_skills": len(skills),
            "skills": skills
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{skill_id}/toggle")
async def skill_toggle(skill_id: str, enable: bool = True):
    """
    เปิด/ปิด Skill
    
    Enable or disable skill.
    
    - skill_id: ID ของ Skill
    - enable: True=เปิด, False=ปิด
    """
    try:
        registry = get_skill_registry()
        
        if enable:
            registry.enable_skill(skill_id)
            message = f"เปิดใช้งาน Skill '{skill_id}' แล้ว"
        else:
            registry.disable_skill(skill_id)
            message = f"ปิดใช้งาน Skill '{skill_id}' แล้ว"
        
        return {
            "success": True,
            "message": message,
            "skill_id": skill_id,
            "enabled": enable
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{skill_id}")
async def skill_delete(skill_id: str):
    """
    ลบ Skill
    
    Delete skill.
    
    - skill_id: ID ของ Skill
    """
    try:
        registry = get_skill_registry()
        registry.delete_skill(skill_id)
        
        return {
            "success": True,
            "message": f"ลบ Skill '{skill_id}' แล้ว",
            "skill_id": skill_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/info")
async def skill_info(skill_id: str):
    """
    ดูข้อมูล Skill
    
    Get skill information.
    """
    try:
        registry = get_skill_registry()
        
        if skill_id not in registry.skills:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        skill = registry.skills[skill_id]
        
        return {
            "success": True,
            "skill": {
                "id": skill_id,
                "name": skill.metadata.name,
                "version": skill.metadata.version,
                "description": skill.metadata.description,
                "author": skill.metadata.author,
                "tags": skill.metadata.tags,
                "enabled": skill.enabled,
                "functions": list(skill.functions.keys())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
