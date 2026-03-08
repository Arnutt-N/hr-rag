# PRP: FastMCP Integration Guide

## 4. FastMCP Integration

### 4.1 What is MCP?

MCP (Model Context Protocol) เป็น open protocol สำหรับการเชื่อมต่อ AI assistants กับ external data sources and tools:

- **Standardized**: มาตรฐานเดียวสำหรับ tools
- **Secure**: Built-in security model
- **Modular**: แยก tools เป็น独立 services
- **Interoperable**: ใช้กับหลาย clients ได้

### 4.2 What is FastMCP?

FastMCP เป็น Python SDK สำหรับสร้าง MCP servers อย่างรวดเร็ว:

```python
from fastmcp import FastMCP

mcp = FastMCP("hr-rag-server")

@mcp.tool()
def search_documents(query: str) -> str:
    """Search HR documents"""
    return results
```

### 4.3 Dependencies

```toml
[tool.poetry.dependencies]
fastmcp = "^0.4.0"
mcp = "^1.0.0"
```

### 4.4 MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Architecture                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │◄────►│  MCP Server │◄────►│   Tools     │
│  (LangChain)│      │  (FastMCP)  │      │  (Functions)│
└─────────────┘      └─────────────┘      └──────┬──────┘
                                                  │
                       ┌──────────────────────────┼──────────┐
                       │                          │          │
                       ▼                          ▼          ▼
                ┌────────────┐           ┌────────────┐ ┌────────┐
                │  Document  │           │   Vector   │ │  SQL   │
                │   Search   │           │    DB      │ │  DB    │
                └────────────┘           └────────────┘ └────────┘
```

### 4.5 MCP Server Implementation

```python
# backend/app/mcp/server.py
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.services.knowledge_base import knowledge_base_service
from app.services.vector_store import vector_store_service
from app.models.database import get_db

# Lifespan context for database connections
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manage application lifecycle"""
    # Startup
    db = await anext(get_db())
    yield {"db": db}
    # Shutdown
    await db.close()

# Create MCP server
mcp = FastMCP(
    "hr-rag-server",
    lifespan=app_lifespan,
    dependencies=["fastmcp", "sqlalchemy", "qdrant-client"]
)

# ==================== TOOLS ====================

@mcp.tool()
async def search_knowledge_base(
    query: str,
    category: str = None,
    limit: int = 5,
    ctx: Context = None
) -> str:
    """
    Search the HR knowledge base for relevant documents.
    
    Args:
        query: Search query in Thai or English
        category: Optional category filter (e.g., "policy", "handbook")
        limit: Maximum number of results (default: 5)
    
    Returns:
        JSON string with search results
    """
    db = ctx.request_context.lifespan_context["db"]
    
    results = await knowledge_base_service.search(
        query=query,
        category=category,
        limit=limit,
        db=db
    )
    
    return json.dumps({
        "query": query,
        "results": [
            {
                "title": r.title,
                "content": r.content[:500],
                "category": r.category,
                "score": r.score
            }
            for r in results
        ]
    }, ensure_ascii=False)


@mcp.tool()
async def get_document_by_id(
    document_id: int,
    ctx: Context = None
) -> str:
    """
    Retrieve a specific document by its ID.
    
    Args:
        document_id: The document ID
    
    Returns:
        Document content and metadata
    """
    db = ctx.request_context.lifespan_context["db"]
    
    doc = await knowledge_base_service.get_document(document_id, db)
    
    if not doc:
        return json.dumps({"error": "Document not found"})
    
    return json.dumps({
        "id": doc.id,
        "title": doc.title,
        "content": doc.content,
        "category": doc.category.name if doc.category else None,
        "tags": doc.tags,
        "created_at": doc.created_at.isoformat()
    }, ensure_ascii=False)


@mcp.tool()
async def list_categories(ctx: Context = None) -> str:
    """
    List all knowledge base categories.
    
    Returns:
        List of categories with document counts
    """
    db = ctx.request_context.lifespan_context["db"]
    
    categories = await knowledge_base_service.list_categories(db)
    
    return json.dumps({
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "document_count": c.document_count
            }
            for c in categories
        ]
    }, ensure_ascii=False)


@mcp.tool()
async def get_user_info(
    user_id: int,
    ctx: Context = None
) -> str:
    """
    Get user information (admin only).
    
    Args:
        user_id: User ID to lookup
    
    Returns:
        User details
    """
    db = ctx.request_context.lifespan_context["db"]
    
    # Check admin permission
    # ...
    
    user = await get_user_by_id(user_id, db)
    
    return json.dumps({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat()
    })


@mcp.tool()
async def get_analytics_summary(
    days: int = 30,
    ctx: Context = None
) -> str:
    """
    Get system analytics summary.
    
    Args:
        days: Number of days to analyze (default: 30)
    
    Returns:
        Analytics data
    """
    db = ctx.request_context.lifespan_context["db"]
    
    stats = await get_analytics(days, db)
    
    return json.dumps({
        "total_users": stats.total_users,
        "total_documents": stats.total_documents,
        "total_queries": stats.total_queries,
        "top_categories": stats.top_categories,
        "period_days": days
    })


@mcp.tool()
async def create_chat_session(
    user_id: int,
    title: str = "New Chat",
    project_id: int = None,
    ctx: Context = None
) -> str:
    """
    Create a new chat session.
    
    Args:
        user_id: User ID
        title: Session title
        project_id: Optional project ID
    
    Returns:
        Session ID
    """
    db = ctx.request_context.lifespan_context["db"]
    
    session = await create_session(
        user_id=user_id,
        title=title,
        project_id=project_id,
        db=db
    )
    
    return json.dumps({
        "session_id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat()
    })


# ==================== RESOURCES ====================

@mcp.resource("docs://policies")
async def get_all_policies() -> str:
    """Get all HR policies as a resource"""
    db = await anext(get_db())
    policies = await knowledge_base_service.get_by_type("policy", db)
    await db.close()
    
    return json.dumps({
        "policies": [{"id": p.id, "title": p.title} for p in policies]
    })


@mcp.resource("docs://handbook")
async def get_employee_handbook() -> str:
    """Get employee handbook content"""
    db = await anext(get_db())
    handbook = await knowledge_base_service.get_by_type("handbook", db)
    await db.close()
    
    if handbook:
        return handbook[0].content
    return "Handbook not found"


@mcp.resource("stats://usage")
async def get_usage_stats() -> str:
    """Get current usage statistics"""
    db = await anext(get_db())
    stats = await get_system_stats(db)
    await db.close()
    
    return json.dumps(stats.__dict__)


# ==================== PROMPTS ====================

@mcp.prompt()
def hr_assistant_prompt() -> str:
    """Default prompt for HR assistant"""
    return """You are an HR assistant for a Thai company. 
You help employees with questions about company policies, benefits, and procedures.
Always respond in Thai unless asked otherwise.
Be polite, professional, and helpful."""


@mcp.prompt()
def policy_expert_prompt(topic: str) -> str:
    """Prompt for policy expert mode"""
    return f"""You are a policy expert specializing in {topic}.
Provide detailed, accurate information based on company policies.
Cite specific policy documents when possible."""


# ==================== SERVER STARTUP ====================

def main():
    """Run MCP server"""
    mcp.run(transport="stdio")  # or "sse" for HTTP

if __name__ == "__main__":
    main()
```

### 4.6 Integration with LangChain

```python
# backend/app/services/mcp_client.py
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientService:
    """Client for connecting to MCP server"""
    
    def __init__(self):
        self.session = None
        self.tools = []
    
    async def connect(self):
        """Connect to MCP server"""
        # Server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "app.mcp.server"],
            env={"DATABASE_URL": settings.database_url}
        )
        
        # Connect
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                
                # Load tools
                self.tools = await load_mcp_tools(session)
                
                return self.tools
    
    async def invoke_tool(self, tool_name: str, **kwargs):
        """Invoke a specific tool"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self.session.call_tool(tool_name, kwargs)
        return result


# Usage with LangChain agent
from langchain.agents import create_tool_calling_agent

async def create_mcp_agent():
    """Create LangChain agent with MCP tools"""
    # Connect to MCP
    mcp_client = MCPClientService()
    tools = await mcp_client.connect()
    
    # Create agent
    llm = ChatOpenAI(model="gpt-4")
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    return agent
```

### 4.7 HTTP Transport (SSE)

```python
# backend/app/mcp/sse_server.py
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

mcp = FastMCP("hr-rag-sse")

# Add tools...
@mcp.tool()
async def search(query: str) -> str:
    return "results"

# SSE setup
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await mcp._mcp_server.run(
            read_stream,
            write_stream,
            mcp._mcp_server.create_initialization_options()
        )

app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=sse.handle_post_message)
    ]
)

# Run with: uvicorn app.mcp.sse_server:app
```

### 4.8 Security Considerations

```python
# backend/app/mcp/auth.py
from fastmcp.auth import BearerAuth

# Add authentication
auth = BearerAuth(
    secret_key=settings.jwt_secret_key,
    algorithm="HS256"
)

mcp = FastMCP(
    "hr-rag-server",
    auth=auth
)

# Validate permissions per tool
@mcp.tool()
async def admin_only_tool(
    ctx: Context = None
) -> str:
    """Tool that requires admin access"""
    token = ctx.request_context.meta.get("auth_token")
    
    # Verify admin role
    if not is_admin(token):
        raise PermissionError("Admin access required")
    
    # Proceed...
```

### 4.9 Benefits of MCP

| Benefit | Description |
|---------|-------------|
| **Standardization** | Tools ใช้มาตรฐานเดียวกัน |
| **Modularity** | แยก tools ออกจาก main app |
| **Security** | Built-in auth and permissions |
| **Discoverability** | Tools self-documenting |
| **Interoperability** | ใช้กับหลาย clients |

### 4.10 Migration Steps

1. **Install FastMCP**
   ```bash
   poetry add fastmcp mcp
   ```

2. **Create MCP Server**
   - Define tools
   - Add resources
   - Create prompts

3. **Expose Existing Functions**
   - Wrap existing services as tools
   - Add type hints and docstrings

4. **Integrate with LangChain**
   - Create MCP client
   - Load tools into agent

5. **Test**
   - Unit tests for tools
   - Integration tests

6. **Deploy**
   - Run as separate service (optional)
   - Or embed in main app

---

*Next: [05-Migration-Plan.md](05-Migration-Plan.md)*