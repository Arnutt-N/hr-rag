"""
Memory Export Skill - Export memories to other AI platforms
Supports: OpenAI, Claude, Gemini, LangChain, and generic formats
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


# Platform-specific export formats
PLATFORM_FORMATS = {
    "openai": {
        "name": "OpenAI / ChatGPT",
        "description": "Export as OpenAI conversation format",
        "format_version": "1.0"
    },
    "claude": {
        "name": "Claude / Anthropic",
        "description": "Export as Claude conversation format",
        "format_version": "1.0"
    },
    "gemini": {
        "name": "Google Gemini",
        "description": "Export as Gemini conversation format",
        "format_version": "1.0"
    },
    "langchain": {
        "name": "LangChain Memory",
        "description": "Export as LangChain chat history",
        "format_version": "1.0"
    },
    "json": {
        "name": "Generic JSON",
        "description": "Standard JSON format",
        "format_version": "1.0"
    },
    "markdown": {
        "name": "Markdown Document",
        "description": "Human-readable markdown",
        "format_version": "1.0"
    }
}


def export_memories(
    memories: List[Dict[str, Any]],
    target_platform: str = "json",
    include_metadata: bool = True,
    filter_tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    ส่งออกความทรงจำ (Memories) ไปยัง AI Platform อื่น
    
    Export memories to other AI platforms.
    
    Args:
        memories: รายการความทรงจำ [{"role", "content", "timestamp", "tags", ...}]
        target_platform: แพลตฟอร์มเป้าหมาย (openai, claude, gemini, langchain, json, markdown)
        include_metadata: รวม metadata
        filter_tags: กรองตาม tags
    
    Returns:
        Exported data in target format
    """
    # Filter memories if tags specified
    if filter_tags:
        memories = [
            m for m in memories
            if any(tag in m.get("tags", []) for tag in filter_tags)
        ]
    
    # Sort by timestamp
    memories = sorted(memories, key=lambda x: x.get("timestamp", ""))
    
    # Export based on platform
    exporters = {
        "openai": _export_openai,
        "claude": _export_claude,
        "gemini": _export_gemini,
        "langchain": _export_langchain,
        "json": _export_json,
        "markdown": _export_markdown
    }
    
    exporter = exporters.get(target_platform, _export_json)
    exported_data = exporter(memories, include_metadata)
    
    return {
        "success": True,
        "platform": target_platform,
        "platform_name": PLATFORM_FORMATS.get(target_platform, {}).get("name", target_platform),
        "exported_count": len(memories),
        "data": exported_data,
        "export_timestamp": datetime.utcnow().isoformat()
    }


def _export_openai(memories: List[Dict], include_metadata: bool) -> Dict[str, Any]:
    """Export in OpenAI format."""
    messages = []
    for memory in memories:
        role_map = {
            "user": "user",
            "assistant": "assistant",
            "system": "system",
            "human": "user",
            "ai": "assistant"
        }
        role = role_map.get(memory.get("role", "user"), "user")
        
        msg = {
            "role": role,
            "content": memory.get("content", "")
        }
        
        if include_metadata:
            msg["metadata"] = {
                "timestamp": memory.get("timestamp"),
                "tags": memory.get("tags", []),
                "session_id": memory.get("session_id")
            }
        
        messages.append(msg)
    
    return {
        "model": "gpt-4",
        "messages": messages,
        "format": "openai-chat"
    }


def _export_claude(memories: List[Dict], include_metadata: bool) -> Dict[str, Any]:
    """Export in Claude format."""
    messages = []
    for memory in memories:
        role_map = {
            "user": "user",
            "assistant": "assistant",
            "human": "user",
            "ai": "assistant"
        }
        role = role_map.get(memory.get("role", "user"), "user")
        
        msg = {
            "role": role,
            "content": [
                {
                    "type": "text",
                    "text": memory.get("content", "")
                }
            ]
        }
        
        if include_metadata:
            msg["metadata"] = {
                "timestamp": memory.get("timestamp"),
                "tags": memory.get("tags", [])
            }
        
        messages.append(msg)
    
    return {
        "model": "claude-3-sonnet",
        "messages": messages,
        "format": "claude-chat"
    }


def _export_gemini(memories: List[Dict], include_metadata: bool) -> Dict[str, Any]:
    """Export in Gemini format."""
    contents = []
    for memory in memories:
        role_map = {
            "user": "user",
            "assistant": "model",
            "human": "user",
            "ai": "model"
        }
        role = role_map.get(memory.get("role", "user"), "user")
        
        content = {
            "role": role,
            "parts": [{"text": memory.get("content", "")}]
        }
        
        contents.append(content)
    
    return {
        "model": "gemini-pro",
        "contents": contents,
        "format": "gemini-chat"
    }


def _export_langchain(memories: List[Dict], include_metadata: bool) -> Dict[str, Any]:
    """Export in LangChain format."""
    messages = []
    for memory in memories:
        msg_type = "HumanMessage" if memory.get("role") in ["user", "human"] else "AIMessage"
        
        msg = {
            "type": msg_type,
            "content": memory.get("content", ""),
            "additional_kwargs": {}
        }
        
        if include_metadata:
            msg["additional_kwargs"] = {
                "timestamp": memory.get("timestamp"),
                "tags": memory.get("tags", [])
            }
        
        messages.append(msg)
    
    return {
        "type": "langchain-chat-history",
        "messages": messages
    }


def _export_json(memories: List[Dict], include_metadata: bool) -> Dict[str, Any]:
    """Export as generic JSON."""
    exported = []
    for memory in memories:
        item = {
            "role": memory.get("role", "user"),
            "content": memory.get("content", ""),
            "timestamp": memory.get("timestamp")
        }
        
        if include_metadata:
            item["metadata"] = {
                "tags": memory.get("tags", []),
                "session_id": memory.get("session_id"),
                "user_id": memory.get("user_id"),
                "source": memory.get("source", "hr-rag")
            }
        
        exported.append(item)
    
    return {
        "format": "generic-json",
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "memories": exported
    }


def _export_markdown(memories: List[Dict], include_metadata: bool) -> str:
    """Export as Markdown document."""
    lines = [
        "# Conversation Export",
        "",
        f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Total Messages: {len(memories)}",
        "",
        "---",
        ""
    ]
    
    for i, memory in enumerate(memories, 1):
        role = memory.get("role", "user").upper()
        content = memory.get("content", "")
        timestamp = memory.get("timestamp", "")
        
        lines.append(f"## Message {i}")
        lines.append(f"**Role:** {role}")
        
        if timestamp:
            lines.append(f"**Time:** {timestamp}")
        
        if include_metadata and memory.get("tags"):
            lines.append(f"**Tags:** {', '.join(memory['tags'])}")
        
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def get_supported_platforms() -> Dict[str, Any]:
    """
    แสดงรายการแพลตฟอร์มที่รองรับ
    
    List supported export platforms.
    
    Returns:
        รายการแพลตฟอร์ม
    """
    return {
        "success": True,
        "platforms": PLATFORM_FORMATS,
        "total": len(PLATFORM_FORMATS)
    }


def validate_export(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ตรวจสอบความถูกต้องของข้อมูลก่อนส่งออก
    
    Validate data before export.
    
    Args:
        data: ข้อมูลที่จะตรวจสอบ
    
    Returns:
        ผลการตรวจสอบ
    """
    errors = []
    warnings = []
    
    memories = data.get("memories", [])
    
    if not memories:
        errors.append("ไม่มีข้อมูลความทรงจำ")
    
    for i, memory in enumerate(memories):
        if not memory.get("content"):
            warnings.append(f"ข้อความที่ {i+1} ว่างเปล่า")
        
        if not memory.get("role"):
            errors.append(f"ข้อความที่ {i+1} ไม่มี role")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "total_memories": len(memories)
    }


# Skill info
def get_info() -> Dict[str, str]:
    """Get skill information."""
    return {
        "name": "Memory Exporter",
        "version": "1.0.0",
        "description": "ส่งออกความทรงจำไปยัง AI Platform อื่น (Export memories to other AI platforms)",
        "author": "HR-RAG Team",
        "supported_platforms": list(PLATFORM_FORMATS.keys()),
        "functions": [
            "export_memories",
            "get_supported_platforms",
            "validate_export"
        ]
    }
