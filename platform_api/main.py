import sys
import os

# Load environment variables from .env FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import logging
import time
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
from shakty3n import load_env_vars, Config

# Import project API
from .database import ProjectDatabase
from .projects import router as projects_router, init_project_api

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("platform_api")

# Global State
agent_manager: Optional[AgentManager] = None
project_db: Optional[ProjectDatabase] = None
DEFAULT_AGENT_ID = "default-agent"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agent_manager, project_db
    logger.info("Initializing AgentManager...")
    load_env_vars() # Load .env file
    
    # Initialize config
    config = Config()
    
    # Store agents in a persistent directory relative to project root
    base_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_projects")
    agent_manager = AgentManager(base_output_dir=base_output_dir)
    
    # Initialize project database
    db_path = os.getenv("DB_PATH", "shakty3n_projects.db")
    logger.info(f"Initializing ProjectDatabase at {db_path}...")
    project_db = ProjectDatabase(db_path)
    
    # Initialize project API with database and config
    init_project_api(project_db, config)
    
    # ========== AUTO-CREATE DEFAULT AGENT ==========
    # This creates a single persistent agent that survives restarts
    logger.info("Creating default agent...")
    default_provider = os.getenv("DEFAULT_AI_PROVIDER", "ollama")
    default_model = os.getenv("DEFAULT_MODEL", "devstral:latest")
    
    try:
        session = agent_manager.spawn_agent(
            name="Shakty3n Assistant",
            provider_name=default_provider,
            model=default_model,
            agent_id=DEFAULT_AGENT_ID  # Fixed ID so frontend can always find it
        )
        logger.info(f"Default agent created: {session.id}")
    except Exception as e:
        logger.error(f"Failed to create default agent: {e}")
    # ================================================

    # Monkeypatch AgentWorkspace to broadcast events
    from shakty3n.agent_manager import AgentWorkspace
    original_record = AgentWorkspace._record_event
    
    def broadcasting_record_event(self, kind: str, message: str, extra: Optional[Dict[str, Any]] = None):
        # Call original
        original_record(self, kind, message, extra)
        # Broadcast
        event = {
            "kind": kind,
            "message": message,
            "extra": extra or {},
            "timestamp": time.time(),
        }
        notify_event(event)
        
    AgentWorkspace._record_event = broadcasting_record_event
    logger.info("AgentWorkspace._record_event patched for broadcasting")
    
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

# Include routers
app.include_router(projects_router)

@app.get("/api/providers/{provider_name}/models")
async def get_provider_models(provider_name: str):
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="AgentManager not initialized")
        
        # Determine provider class
        from shakty3n.ai_providers import OpenAIProvider, AnthropicProvider, GoogleProvider, OllamaProvider, DockerModelRunnerProvider
        
        provider_map = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "google": GoogleProvider,
            "ollama": OllamaProvider
        }
        
        provider_class = provider_map.get(provider_name.lower())
        if not provider_class:
            raise HTTPException(status_code=404, detail="Provider not found")
             
        # Instantiate provider to get models (requires API keys usually, but Ollama doesn't need much)
        # For remote providers, we ideally want to fetch models without full instantiation if possible,
        # or use a check method. But for now, we try instantiation.
        # Note: This might fail if keys are missing for remote providers.
        # We can handle Ollama specifically or try generic catch.
        
        # For simplicity in this fix, we'll just try to get models if possible
        # or return the hardcoded list if we can't connect, but for Ollama we really want the dynamic list
        
        if provider_name.lower() == "ollama":
            # Initialize with default/env settings
            p = OllamaProvider()
            models = p.get_available_models()
            return {"models": models}
             
        if provider_name.lower() == "docker":
            # Docker Model Runner
            p = DockerModelRunnerProvider()
            models = p.get_available_models()
            return {"models": models}
             
        # For others, we might stick to defaults or implement dynamic fetching later
        # Returning empty list will signal frontend to use its defaults
        return {"models": []}
        
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return {"models": []}

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

class ProcessMessageRequest(BaseModel):
    """Request to process a user message with intent classification"""
    content: str
    provider: str = "ollama"
    model: Optional[str] = None

class ProcessMessageResponse(BaseModel):
    """Response from processing a user message"""
    intent: str  # greeting, question, command, project_creation, clarification
    response: str  # AI's message to display
    action: Optional[str] = None  # null, run_code, create_project, analyze_code
    requires_confirmation: bool = False
    project_config: Optional[Dict[str, Any]] = None  # {description, type, requirements}


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
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(
                    "WebSocket broadcast failed to %s (active: %d): %s",
                    getattr(connection, "client", "unknown"),
                    len(self.active_connections),
                    e
                )
                self.active_connections.remove(connection)

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

class ResumeAgentRequest(BaseModel):
    path: str
    provider: str = "ollama"
    model: Optional[str] = None

@app.post("/api/agents/resume")
async def resume_agent(request: ResumeAgentRequest):
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    
    # Verify path exists
    full_path = os.path.join(agent_manager.base_output_dir, request.path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Project directory not found")
    
    # Determine provider and model from database or request
    provider = request.provider
    model = request.model
    
    # Try to get saved settings from database
    if project_db:
        project = project_db.get_project_by_path(full_path)
        if project:
            # Use saved settings if request doesn't specify
            if not model and project.get("model"):
                model = project["model"]
            if project.get("provider"):
                provider = project["provider"]
        
    # Check if already loaded - but recreate with correct provider/model
    for session in agent_manager.agents.values():
        if session.workspace.root_dir == full_path:
            # Update provider if different
            if session.provider_name != provider or session.model != model:
                # Remove old session and create new one with correct settings
                del agent_manager.agents[session.id]
                break
            return {
                "id": session.id,
                "name": session.name,
                "status": session.status,
                "provider": session.provider_name,
                "model": session.model
            }
             
    # Spawn new agent wrapper around existing dir
    session = agent_manager.spawn_agent(
        name=request.path,
        provider_name=provider,
        model=model,
        output_dir=full_path
    )
    
    # Save settings to database for next time
    if project_db:
        project = project_db.get_project_by_path(full_path)
        if project:
            project_db.update_project_model(project["id"], provider, model or "deepseek-coder:6.7b")
    
    return {
        "id": session.id,
        "name": session.name,
        "status": session.status,
        "provider": session.provider_name,
        "model": session.model
    }

@app.get("/api/local-projects")
async def list_local_projects():
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
        
    projects = []
    base_dir = agent_manager.base_output_dir
    if os.path.exists(base_dir):
        for name in os.listdir(base_dir):
            path = os.path.join(base_dir, name)
            if os.path.isdir(path) and not name.startswith('.'):
                projects.append(name)
                 
    return {"projects": projects}

class SwitchWorkspaceRequest(BaseModel):
    """Request to switch agent workspace to a different folder"""
    path: str  # Folder path (relative to generated_projects or absolute)
    model: Optional[str] = None

@app.post("/api/agents/{agent_id}/switch-workspace")
async def switch_workspace(agent_id: str, request: SwitchWorkspaceRequest):
    """Switch the agent's workspace to a different folder"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Resolve the path
    folder_path = request.path
    if not os.path.isabs(folder_path):
        # Relative path - try generated_projects first
        folder_path = os.path.join(agent_manager.base_output_dir, request.path)
    
    # Check for /external mount (Docker volume for external projects)
    if not os.path.exists(folder_path):
        external_path = os.path.join("/external", request.path)
        if os.path.exists(external_path):
            folder_path = external_path
    
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail=f"Folder not found: {request.path}")
    
    # Update session workspace
    from shakty3n.agent_manager import AgentWorkspace
    from shakty3n.executor import AutonomousExecutor
    
    session.workspace = AgentWorkspace(folder_path)
    session.executor = AutonomousExecutor(session.executor.ai_provider, output_dir=folder_path)
    session.name = os.path.basename(folder_path)
    
    # Update model if specified
    if request.model:
        from shakty3n.ai_providers import AIProviderFactory
        session.model = request.model
        new_provider = AIProviderFactory.create_provider(session.provider_name, model=request.model)
        session.executor.ai_provider = new_provider
    
    logger.info(f"Switched agent {agent_id} workspace to: {folder_path}")
    
    return {
        "status": "switched",
        "agent_id": agent_id,
        "workspace": folder_path,
        "name": session.name
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

# ==================== Intelligent Message Processing ====================

INTENT_CLASSIFICATION_PROMPT = """You are an intelligent assistant for Shakty3n, an autonomous coding platform.
Analyze the user's message and classify their intent, then respond appropriately.

INTENTS:
1. GREETING - Hello, hi, thanks, bye, etc. → Respond friendly and helpful
2. QUESTION - How to, what is, explain, help with, etc. → Answer the question helpfully
3. COMMAND - Run the code, test it, deploy, start server, install, etc. → Acknowledge and prepare to execute
4. PROJECT_CREATION - Build an app, create a website, make a todo app, etc. → Confirm requirements first
5. CLARIFICATION - Vague requests that need more info → Ask for specific details

CONTEXT:
- The user is working in an IDE workspace with code files
- They can run terminal commands, edit files, and create projects
- Be helpful but don't start creating projects without confirmation

You MUST respond with ONLY a valid JSON object in this exact format:
{
  "intent": "greeting|question|command|project_creation|clarification",
  "response": "Your friendly response message here",
  "action": null,
  "requires_confirmation": false,
  "project_config": null
}

For PROJECT_CREATION intent, set:
- requires_confirmation: true
- project_config: {"description": "...", "type": "web-react|android|ios|flutter|etc", "requirements": {}}

For COMMAND intent, set:
- action: "run_code" or "run_command"

USER MESSAGE: """

@app.post("/api/agents/{agent_id}/process", response_model=ProcessMessageResponse)
async def process_message(agent_id: str, request: ProcessMessageRequest):
    """
    Intelligently process a user message with intent classification.
    Reasons before acting - won't create projects for simple greetings.
    """
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    user_message = request.content.strip()
    
    # Build context about current workspace
    workspace_context = ""
    try:
        root_path = Path(session.workspace.root_dir)
        files = list(root_path.rglob("*"))[:20]  # First 20 files
        if files:
            file_list = [str(f.relative_to(root_path)) for f in files if f.is_file()]
            workspace_context = f"\n\nCurrent workspace files: {', '.join(file_list[:10])}"
    except:
        pass
    
    # Use the AI provider to classify intent
    try:
        from shakty3n.ai_providers import AIProviderFactory
        
        provider_name = request.provider or session.provider_name
        model = request.model or session.model
        
        # Create provider instance
        provider = AIProviderFactory.create_provider(provider_name, model=model)
        
        # Build the prompt
        full_prompt = INTENT_CLASSIFICATION_PROMPT + user_message + workspace_context
        
        # Get AI response
        ai_response = provider.generate(full_prompt)
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', ai_response)
        if json_match:
            parsed = json.loads(json_match.group())
            
            # Validate and return
            return ProcessMessageResponse(
                intent=parsed.get("intent", "clarification"),
                response=parsed.get("response", "I'm not sure how to help with that. Could you clarify?"),
                action=parsed.get("action"),
                requires_confirmation=parsed.get("requires_confirmation", False),
                project_config=parsed.get("project_config")
            )
        else:
            # Failed to parse, return a safe response
            logger.warning(f"Failed to parse AI response: {ai_response}")
            return ProcessMessageResponse(
                intent="clarification",
                response="I understood your message but need a moment to think. Could you rephrase that?",
                action=None,
                requires_confirmation=False,
                project_config=None
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return ProcessMessageResponse(
            intent="clarification",
            response="I had trouble understanding. Could you try rephrasing your request?",
            action=None,
            requires_confirmation=False,
            project_config=None
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Fallback to simple keyword matching if AI fails
        lower_msg = user_message.lower()
        
        if any(word in lower_msg for word in ["hello", "hi", "hey", "thanks", "thank you", "bye"]):
            return ProcessMessageResponse(
                intent="greeting",
                response="Hello! I'm your Shakty3n assistant. How can I help you today?",
                action=None,
                requires_confirmation=False,
                project_config=None
            )
        elif any(word in lower_msg for word in ["how", "what", "why", "explain", "help"]):
            return ProcessMessageResponse(
                intent="question",
                response=f"I'd be happy to help! Let me think about your question: '{user_message}'",
                action=None,
                requires_confirmation=False,
                project_config=None
            )
        elif any(word in lower_msg for word in ["run", "execute", "start", "test"]):
            return ProcessMessageResponse(
                intent="command",
                response="I'll help you run that. What specific command would you like me to execute?",
                action="run_code",
                requires_confirmation=False,
                project_config=None
            )
        elif any(word in lower_msg for word in ["build", "create", "make", "develop", "app", "website"]):
            return ProcessMessageResponse(
                intent="project_creation",
                response=f"I can help you create that! Before I start, let me confirm: You want me to build '{user_message}'. Is that correct?",
                action="create_project",
                requires_confirmation=True,
                project_config={
                    "description": user_message,
                    "type": "web-react",
                    "requirements": {}
                }
            )
        else:
            return ProcessMessageResponse(
                intent="clarification", 
                response="I'm here to help! Could you tell me more about what you'd like to do?",
                action=None,
                requires_confirmation=False,
                project_config=None
            )


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

# ==================== Chat History Endpoints ====================

class ChatMessageRequest(BaseModel):
    role: str
    content: str

@app.get("/api/agents/{agent_id}/chat")
async def get_chat_history(agent_id: str, limit: int = 100):
    """Get chat history for an agent/project"""
    if not project_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Try to find project by agent ID or path
    if agent_manager:
        session = agent_manager.agents.get(agent_id)
        if session:
            # Look up project by path
            project = project_db.get_project_by_path(session.workspace.root_dir)
            if project:
                history = project_db.get_chat_history(project["id"], limit=limit)
                return {"history": history, "project_id": project["id"]}
    
    # Fallback: return empty history
    return {"history": [], "project_id": None}

@app.post("/api/agents/{agent_id}/chat")
async def add_chat_message(agent_id: str, request: ChatMessageRequest):
    """Add a message to chat history"""
    if not project_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AgentManager not initialized")
    
    session = agent_manager.agents.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Look up or create project
    project = project_db.get_project_by_path(session.workspace.root_dir)
    if not project:
        # Create project entry if missing
        project_id = agent_id
        project_db.create_project(
            project_id=project_id,
            description=session.name,
            project_type="web",
            provider=session.provider_name,
            model=session.model
        )
        project_db.update_artifact_path(project_id, session.workspace.root_dir)
    else:
        project_id = project["id"]
    
    # Add message
    msg_id = project_db.add_chat_message(project_id, request.role, request.content)
    
    return {"id": msg_id, "project_id": project_id}

@app.delete("/api/agents/{agent_id}/chat")
async def clear_chat_history(agent_id: str):
    """Clear chat history for an agent/project"""
    if not project_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    if agent_manager:
        session = agent_manager.agents.get(agent_id)
        if session:
            project = project_db.get_project_by_path(session.workspace.root_dir)
            if project:
                project_db.clear_chat_history(project["id"])
                return {"status": "cleared"}
    
    return {"status": "no history found"}

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

