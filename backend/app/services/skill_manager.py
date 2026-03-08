"""
Skill Management System - Create, import, and use skills
"""

import os
import json
import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable, Type
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    name: str
    version: str
    description: str
    author: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Skill:
    """Represents a skill with metadata and functionality."""
    metadata: SkillMetadata
    module: Any = None
    functions: Dict[str, Callable] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class SkillRegistry:
    """
    Central registry for managing skills.
    
    Features:
    - Register/unregister skills
    - Import skills from files
    - Create new skills
    - Execute skill functions
    """
    
    def __init__(self, skills_dir: Optional[str] = None):
        """
        Initialize skill registry.
        
        Args:
            skills_dir: Directory to store/load skills
        """
        self.skills: Dict[str, Skill] = {}
        self.skills_dir = skills_dir or os.path.expanduser("~/.hr-rag/skills")
        self.plugins_dir = os.path.join(self.skills_dir, "plugins")
        
        # Create directories
        os.makedirs(self.skills_dir, exist_ok=True)
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        # Auto-load skills
        self._auto_load_skills()
    
    def _auto_load_skills(self):
        """Automatically load skills from skills directory."""
        skills_file = os.path.join(self.skills_dir, "skills.json")
        if os.path.exists(skills_file):
            with open(skills_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for skill_data in data.get("skills", []):
                    try:
                        self.import_skill(skill_data["path"])
                    except Exception as e:
                        print(f"Failed to load skill {skill_data.get('name')}: {e}")
    
    def create_skill(
        self,
        name: str,
        description: str,
        author: str,
        template: str = "basic",
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """
        Create a new skill from template.
        
        Args:
            name: Skill name
            description: Skill description
            author: Author name
            template: Template type (basic, api, mcp, agent)
            tags: Skill tags
            dependencies: Required dependencies
        
        Returns:
            Path to created skill
        """
        # Sanitize name
        skill_id = name.lower().replace(" ", "_").replace("-", "_")
        skill_path = os.path.join(self.skills_dir, skill_id)
        
        if os.path.exists(skill_path):
            raise ValueError(f"Skill '{name}' already exists")
        
        # Create directory structure
        os.makedirs(skill_path, exist_ok=True)
        os.makedirs(os.path.join(skill_path, "src"), exist_ok=True)
        os.makedirs(os.path.join(skill_path, "tests"), exist_ok=True)
        
        # Create metadata
        metadata = SkillMetadata(
            name=name,
            version="1.0.0",
            description=description,
            author=author,
            tags=tags or [],
            dependencies=dependencies or []
        )
        
        # Create skill.json
        with open(os.path.join(skill_path, "skill.json"), 'w', encoding='utf-8') as f:
            json.dump({
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "tags": metadata.tags,
                "dependencies": metadata.dependencies,
                "entry_point": "src/main.py",
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at
            }, f, indent=2, ensure_ascii=False)
        
        # Create skill code from template
        self._create_skill_template(skill_path, skill_id, template, metadata)
        
        # Register skill
        skill = Skill(metadata=metadata, config={})
        self.skills[skill_id] = skill
        
        self._save_registry()
        
        return skill_path
    
    def _create_skill_template(
        self,
        skill_path: str,
        skill_id: str,
        template: str,
        metadata: SkillMetadata
    ):
        """Create skill files from template."""
        
        templates = {
            "basic": self._get_basic_template,
            "api": self._get_api_template,
            "mcp": self._get_mcp_template,
            "agent": self._get_agent_template
        }
        
        template_func = templates.get(template, self._get_basic_template)
        code = template_func(skill_id, metadata)
        
        # Write main.py
        with open(os.path.join(skill_path, "src", "main.py"), 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Write __init__.py
        with open(os.path.join(skill_path, "src", "__init__.py"), 'w', encoding='utf-8') as f:
            f.write(f"""\"\"\"
{metadata.name} - {metadata.description}
\"\"\"

from .main import *

__version__ = "{metadata.version}"
__author__ = "{metadata.author}"
""")
        
        # Write README.md
        with open(os.path.join(skill_path, "README.md"), 'w', encoding='utf-8') as f:
            f.write(f"""# {metadata.name}

{metadata.description}

## Author
{metadata.author}

## Version
{metadata.version}

## Tags
{', '.join(metadata.tags) if metadata.tags else 'None'}

## Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage
```python
from src.main import *

# Use skill functions
result = main()
```
""")
        
        # Write requirements.txt
        with open(os.path.join(skill_path, "requirements.txt"), 'w', encoding='utf-8') as f:
            for dep in metadata.dependencies:
                f.write(f"{dep}\n")
    
    def _get_basic_template(self, skill_id: str, metadata: SkillMetadata) -> str:
        """Get basic skill template."""
        return f'''"""
{metadata.name} - {metadata.description}
Author: {metadata.author}
Version: {metadata.version}
"""

from typing import Dict, Any, Optional


def main(**kwargs) -> Dict[str, Any]:
    """
    Main function for {skill_id} skill.
    
    Args:
        **kwargs: Arguments
    
    Returns:
        Result dictionary
    """
    # TODO: Implement skill logic
    return {{
        "success": True,
        "message": "{metadata.name} executed successfully",
        "data": {{}}
    }}


def get_info() -> Dict[str, str]:
    """Get skill information."""
    return {{
        "name": "{metadata.name}",
        "version": "{metadata.version}",
        "description": "{metadata.description}",
        "author": "{metadata.author}"
    }}
'''
    
    def _get_api_template(self, skill_id: str, metadata: SkillMetadata) -> str:
        """Get API skill template."""
        return f'''"""
{metadata.name} - API Integration Skill
Author: {metadata.author}
Version: {metadata.version}
"""

import httpx
from typing import Dict, Any, Optional


class {skill_id.title().replace("_", "")}API:
    """API client for {metadata.name}."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def call_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call API endpoint."""
        headers = {{}}
        if self.api_key:
            headers["Authorization"] = f"Bearer {{self.api_key}}"
        
        response = await self.client.post(
            f"{{self.base_url}}{{endpoint}}",
            json=data,
            headers=headers
        )
        return response.json()


async def main(api_key: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Main function."""
    client = {skill_id.title().replace("_", "")}API(api_key=api_key)
    # TODO: Implement API calls
    return {{"success": True, "data": {{}}}}
'''
    
    def _get_mcp_template(self, skill_id: str, metadata: SkillMetadata) -> str:
        """Get MCP skill template."""
        return f'''"""
{metadata.name} - MCP Tool Skill
Author: {metadata.author}
Version: {metadata.version}
"""

from fastmcp import FastMCP
from typing import Dict, Any

mcp = FastMCP("{skill_id}")


@mcp.tool()
async def {skill_id}_tool(input_data: str) -> str:
    """
    Tool for {metadata.name}.
    
    Args:
        input_data: Input data
    
    Returns:
        Result
    """
    # TODO: Implement tool logic
    return f"Processed: {{input_data}}"


def main():
    """Run MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
'''
    
    def _get_agent_template(self, skill_id: str, metadata: SkillMetadata) -> str:
        """Get agent skill template."""
        return f'''"""
{metadata.name} - AI Agent Skill
Author: {metadata.author}
Version: {metadata.version}
"""

from typing import Dict, Any, List
from app.services.llm.langchain_service import get_llm_service


class {skill_id.title().replace("_", "")}Agent:
    """AI Agent for {metadata.name}."""
    
    def __init__(self):
        self.llm = get_llm_service()
    
    async def process(self, task: str, context: List[str]) -> Dict[str, Any]:
        """Process task."""
        prompt = f"""Task: {{task}}
Context: {{'\\n'.join(context)}}

Result:"""
        
        response = await self.llm.chat([{{"role": "user", "content": prompt}}])
        return {{"success": True, "result": response}}


async def main(task: str, context: List[str] = None) -> Dict[str, Any]:
    """Main function."""
    agent = {skill_id.title().replace("_", "")}Agent()
    return await agent.process(task, context or [])
'''
    
    def import_skill(self, skill_path: str) -> Skill:
        """
        Import skill from path.
        
        Args:
            skill_path: Path to skill directory
        
        Returns:
            Imported Skill
        """
        skill_json = os.path.join(skill_path, "skill.json")
        
        if not os.path.exists(skill_json):
            raise ValueError(f"Skill not found at {skill_path}")
        
        # Load metadata
        with open(skill_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = SkillMetadata(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", [])
        )
        
        # Import module
        src_path = os.path.join(skill_path, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        try:
            module = importlib.import_module("main")
            importlib.reload(module)  # Reload if already imported
        except Exception as e:
            raise ImportError(f"Failed to import skill module: {e}")
        
        # Extract functions
        functions = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith("_"):
                functions[name] = obj
        
        # Create skill
        skill = Skill(
            metadata=metadata,
            module=module,
            functions=functions,
            config=data.get("config", {})
        )
        
        self.skills[skill_id] = skill
        self._save_registry()
        
        return skill
    
    def use_skill(self, skill_id: str, function_name: str = "main", **kwargs) -> Any:
        """
        Execute a skill function.
        
        Args:
            skill_id: Skill identifier
            function_name: Function to call
            **kwargs: Arguments
        
        Returns:
            Function result
        """
        if skill_id not in self.skills:
            raise ValueError(f"Skill '{skill_id}' not found")
        
        skill = self.skills[skill_id]
        
        if not skill.enabled:
            raise RuntimeError(f"Skill '{skill_id}' is disabled")
        
        if function_name not in skill.functions:
            raise ValueError(f"Function '{function_name}' not found in skill '{skill_id}'")
        
        func = skill.functions[function_name]
        return func(**kwargs)
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """List all registered skills."""
        return [
            {
                "id": skill_id,
                "name": skill.metadata.name,
                "version": skill.metadata.version,
                "description": skill.metadata.description,
                "enabled": skill.enabled,
                "functions": list(skill.functions.keys())
            }
            for skill_id, skill in self.skills.items()
        ]
    
    def disable_skill(self, skill_id: str):
        """Disable a skill."""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = False
            self._save_registry()
    
    def enable_skill(self, skill_id: str):
        """Enable a skill."""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = True
            self._save_registry()
    
    def delete_skill(self, skill_id: str):
        """Delete a skill."""
        if skill_id in self.skills:
            del self.skills[skill_id]
            self._save_registry()
    
    def _save_registry(self):
        """Save registry to disk."""
        skills_file = os.path.join(self.skills_dir, "skills.json")
        with open(skills_file, 'w', encoding='utf-8') as f:
            json.dump({
                "skills": [
                    {
                        "id": skill_id,
                        "path": os.path.join(self.skills_dir, skill_id),
                        "enabled": skill.enabled
                    }
                    for skill_id, skill in self.skills.items()
                ]
            }, f, indent=2, ensure_ascii=False)


# Singleton
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get skill registry singleton."""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
