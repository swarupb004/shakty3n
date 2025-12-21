import sys
import os
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add local src to path to import shakty3n
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from shakty3n.agent_manager import AgentManager, AgentSession
from shakty3n import load_env_vars

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("platform_api")

# Global State
agent_manager: Optional[AgentManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agent_manager
    logger.info("Initializing AgentManager...")
    load_env_vars() # Load .env file
    # Store agents in a persistent directory relative to project root
    base_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_projects")
    agent_manager = AgentManager(base_output_dir=base_output_dir)
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(title="Shakty3n Platform API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class CreateAgentRequest(BaseModel):
    name: str
    provider: str = "openai"
    model: Optional[str] = None

class WorkflowRequest(BaseModel):
    description: str
    project_type: str
    requirements: Dict[str, Any] = {}
    generate_tests: bool = False
    validate_code: bool = False

class TerminalCommandRequest(BaseModel):
    command: str

class FileWriteRequest(BaseModel):
    content: str

# --- WebSocket Manager ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/dashboard")
async def get_dashboard():
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    return agent_manager.get_dashboard_snapshot()

@app.post("/api/agents")
async def create_agent(request: CreateAgentRequest):
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    session = agent_manager.spawn_agent(
        name=request.name,
        provider_name=request.provider,
        model=request.model
    )
    return {
        "id": session.id,
        "name": session.name,
        "status": session.status,
        "provider": session.provider_name
    }

@app.post("/api/agents/{agent_id}/workflow")
async def run_workflow(agent_id: str, request: WorkflowRequest):
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Run in background to not block
    asyncio.create_task(
        agent_manager.run_workflow(
            agent=session,
            description=request.description,
            project_type=request.project_type,
            requirements=request.requirements,
            generate_tests=request.generate_tests,
            validate_code=request.validate_code
        )
    )
    
    return {"status": "started", "agent_id": agent_id}

@app.get("/api/agents/{agent_id}/workspace/files")
async def list_files(agent_id: str, path: str = "."):
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Simple recursive walker
    tree = []
    root_path = Path(session.workspace.root_dir).resolve()
    
    for root, dirs, files in os.walk(root_path):
        # Skip git and hidden
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        rel_root = os.path.relpath(root, root_path)
        if rel_root == ".":
            rel_root = ""
            
        for d in dirs:
            tree.append({
                "name": d,
                "type": "directory",
                "path": os.path.join(rel_root, d).replace("\\", "/")
            })
        for f in files:
            tree.append({
                "name": f,
                "type": "file",
                "path": os.path.join(rel_root, f).replace("\\", "/")
            })
            
    # Sort: directories first, then files
    tree.sort(key=lambda x: (x["type"] != "directory", x["path"]))
    return tree

class DirectoryCreateRequest(BaseModel):
    path: str

@app.post("/api/agents/{agent_id}/workspace/directory")
async def create_directory(agent_id: str, request: DirectoryCreateRequest):
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    try:
        full_path = session.workspace._resolve_path(request.path)
        os.makedirs(full_path, exist_ok=True)
        return {"status": "created", "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/agents/{agent_id}/workspace/content")
async def read_file(agent_id: str, path: str):
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        content = session.workspace.open_file(path)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/agents/{agent_id}/workspace/content")
async def save_file(agent_id: str, path: str, request: FileWriteRequest):
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    try:
        session.workspace.save_file(path, request.content)
        return {"status": "saved", "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive and simple echo/command handling if needed
            # For now just push events
            data = await websocket.receive_text()
            # We could handle client-sent events here
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Note: In a real implementation, we would hook into AgentWorkspace._record_event 
# to broadcast via `manager.broadcast()`.
# For this prototype, we'll patch the method dynamically or assume polling for now/simple implementation.

def notify_event(event: Dict[str, Any]):
    # simple monkeypatch hook
    asyncio.create_task(manager.broadcast(json.dumps(event)))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
