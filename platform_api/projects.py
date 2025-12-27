"""
Project orchestration API endpoints
"""
import sys
import os
import asyncio
import uuid
import shutil
import zipfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Header, Response
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Add local src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from shakty3n import AIProviderFactory, AutonomousExecutor, load_env_vars, Config
from .database import ProjectDatabase, ProjectStatus

logger = logging.getLogger("project_api")

# Global instances
db: Optional[ProjectDatabase] = None
config: Optional[Config] = None

# Simple auth token (optional)
AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "")


def get_auth_token(authorization: str = Header(None)) -> Optional[str]:
    """Extract and validate auth token if enabled"""
    if not AUTH_TOKEN:
        return None  # Auth disabled
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Support "Bearer <token>" or just "<token>"
    token = authorization.replace("Bearer ", "").strip()
    
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return token


router = APIRouter(prefix="/api/projects", tags=["projects"])


# Request/Response Models
class CreateProjectRequest(BaseModel):
    description: str
    project_type: str
    provider: str = "openai"
    model: Optional[str] = None
    with_tests: bool = False
    validate_code: bool = False


class ProjectResponse(BaseModel):
    id: str
    description: str
    project_type: str
    provider: str
    model: Optional[str]
    status: str
    with_tests: bool
    validate_code: bool
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    artifact_path: Optional[str]
    error_message: Optional[str]


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    token: Optional[str] = Depends(get_auth_token)
):
    """Create and start a new project run"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Generate unique project ID
    project_id = f"proj_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    
    # Create project in database
    project = db.create_project(
        project_id=project_id,
        description=request.description,
        project_type=request.project_type,
        provider=request.provider,
        model=request.model,
        with_tests=request.with_tests,
        validate=request.validate_code
    )
    
    # Start execution in background
    asyncio.create_task(
        execute_project_async(
            project_id=project_id,
            description=request.description,
            project_type=request.project_type,
            provider=request.provider,
            model=request.model,
            with_tests=request.with_tests,
            validate=request.validate_code
        )
    )
    
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token: Optional[str] = Depends(get_auth_token)
):
    """List all projects"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    projects = db.list_projects(status=status, limit=limit, offset=offset)
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    token: Optional[str] = Depends(get_auth_token)
):
    """Get project metadata and status"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.get("/{project_id}/logs")
async def get_project_logs(
    project_id: str,
    token: Optional[str] = Depends(get_auth_token)
):
    """Stream project logs via Server-Sent Events"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    async def event_generator():
        """Generate SSE events from log file"""
        log_file = project.get("log_file")
        
        if not log_file or not os.path.exists(log_file):
            # Send initial message
            yield {
                "event": "log",
                "data": f"Waiting for logs... (Status: {project['status']})"
            }
            
            # Poll for log file creation
            for _ in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                updated_project = db.get_project(project_id)
                log_file = updated_project.get("log_file")
                if log_file and os.path.exists(log_file):
                    break
            else:
                yield {
                    "event": "error",
                    "data": "Log file not found"
                }
                return
        
        # Stream log file
        with open(log_file, "r") as f:
            position = 0
            while True:
                # Read new content
                f.seek(position)
                new_content = f.read()
                
                if new_content:
                    # Send new lines
                    for line in new_content.splitlines():
                        yield {
                            "event": "log",
                            "data": line
                        }
                    position = f.tell()
                
                # Check if project is complete
                updated_project = db.get_project(project_id)
                if updated_project["status"] in [ProjectStatus.DONE, ProjectStatus.FAILED]:
                    yield {
                        "event": "status",
                        "data": updated_project["status"]
                    }
                    break
                
                # Wait before next poll
                await asyncio.sleep(0.5)
    
    return EventSourceResponse(event_generator())


@router.get("/{project_id}/artifact")
async def download_artifact(
    project_id: str,
    token: Optional[str] = Depends(get_auth_token)
):
    """Download project artifact as zip"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    artifact_path = project.get("artifact_path")
    if not artifact_path or not os.path.exists(artifact_path):
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Create zip if directory
    if os.path.isdir(artifact_path):
        zip_path = f"/tmp/{project_id}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(artifact_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, artifact_path)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{project_id}.zip"
        )
    
    return FileResponse(artifact_path)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    token: Optional[str] = Depends(get_auth_token)
):
    """Delete project and cleanup files"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Cleanup files
    if project.get("artifact_path") and os.path.exists(project["artifact_path"]):
        if os.path.isdir(project["artifact_path"]):
            shutil.rmtree(project["artifact_path"], ignore_errors=True)
        else:
            os.remove(project["artifact_path"])
    
    if project.get("log_file") and os.path.exists(project["log_file"]):
        os.remove(project["log_file"])
    
    # Delete from database
    db.delete_project(project_id)
    
    return {"status": "deleted", "id": project_id}


@router.post("/{project_id}/retry")
async def retry_project(
    project_id: str,
    token: Optional[str] = Depends(get_auth_token)
):
    """Retry a failed project"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project["status"] != ProjectStatus.FAILED:
        raise HTTPException(status_code=400, detail="Can only retry failed projects")
    
    # Reset status
    db.update_status(project_id, ProjectStatus.PLANNING, error_message=None)
    
    # Start execution in background
    asyncio.create_task(
        execute_project_async(
            project_id=project_id,
            description=project["description"],
            project_type=project["project_type"],
            provider=project["provider"],
            model=project.get("model"),
            with_tests=project["with_tests"],
            validate=project["validate"]
        )
    )
    
    return {"status": "retrying", "id": project_id}


async def execute_project_async(
    project_id: str,
    description: str,
    project_type: str,
    provider: str,
    model: Optional[str],
    with_tests: bool,
    validate: bool
):
    """Execute project in background"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "project_logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{project_id}.log")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_projects")
    
    # Update log file in database
    db.update_log_file(project_id, log_file)
    
    try:
        # Open log file
        with open(log_file, "w") as log:
            log.write(f"Starting project execution: {project_id}\n")
            log.write(f"Description: {description}\n")
            log.write(f"Type: {project_type}\n")
            log.write(f"Provider: {provider}\n")
            log.write(f"Model: {model}\n\n")
            log.flush()
            
            # Update status to generating
            db.update_status(project_id, ProjectStatus.GENERATING)
            log.write(f"Status: {ProjectStatus.GENERATING}\n")
            log.flush()
            
            # Get AI provider
            if not config:
                raise Exception("Config not initialized")
            
            provider_config = config.get_provider_config(provider)
            api_key = provider_config.get("api_key")
            model = model or provider_config.get("model")
            
            log.write(f"Initializing AI provider...\n")
            log.flush()
            
            ai_provider = AIProviderFactory.create_provider(provider, api_key, model)
            
            # Create executor
            executor = AutonomousExecutor(ai_provider, output_dir)
            
            log.write(f"Starting autonomous execution...\n\n")
            log.flush()
            
            # Execute project (this will print to stdout, we capture it)
            # For now, we'll run synchronously in the async context
            # In production, you'd want to run this in a proper background worker
            result = await asyncio.to_thread(
                executor.execute_project,
                description=description,
                project_type=project_type,
                requirements={},
                generate_tests=with_tests,
                validate_code=validate
            )
            
            log.write(f"\n\nExecution completed\n")
            log.write(f"Success: {result.get('success')}\n")
            log.flush()
            
            if result.get("success"):
                # Update status to done
                artifact_path = result.get("generation", {}).get("output_dir")
                db.update_status(project_id, ProjectStatus.DONE)
                if artifact_path:
                    db.update_artifact_path(project_id, artifact_path)
                    log.write(f"Artifact path: {artifact_path}\n")
                    log.flush()
            else:
                # Update status to failed
                error_msg = result.get("error", "Unknown error")
                db.update_status(project_id, ProjectStatus.FAILED, error_message=error_msg)
                log.write(f"Error: {error_msg}\n")
                log.flush()
                
    except Exception as e:
        logger.error(f"Error executing project {project_id}: {e}", exc_info=True)
        
        # Write error to log
        with open(log_file, "a") as log:
            log.write(f"\n\nFATAL ERROR: {str(e)}\n")
        
        # Update status to failed
        db.update_status(project_id, ProjectStatus.FAILED, error_message=str(e))


def init_project_api(database: ProjectDatabase, app_config: Config):
    """Initialize project API with database and config"""
    global db, config
    db = database
    config = app_config
