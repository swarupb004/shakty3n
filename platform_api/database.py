"""
SQLite database for project run persistence
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    GENERATING = "generating"
    VALIDATING = "validating"
    DONE = "done"
    FAILED = "failed"


class ProjectDatabase:
    """SQLite database for storing project runs"""
    
    def __init__(self, db_path: str = "shakty3n_projects.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT,
                    status TEXT NOT NULL,
                    with_tests BOOLEAN DEFAULT 0,
                    validate BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    log_file TEXT,
                    artifact_path TEXT,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
    
    def create_project(
        self,
        project_id: str,
        description: str,
        project_type: str,
        provider: str,
        model: Optional[str] = None,
        with_tests: bool = False,
        validate: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new project run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO projects 
                (id, description, project_type, provider, model, status, 
                 with_tests, validate, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    description,
                    project_type,
                    provider,
                    model,
                    ProjectStatus.PLANNING,
                    with_tests,
                    validate,
                    json.dumps(metadata or {})
                )
            )
            conn.commit()
        
        return self.get_project(project_id)
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM projects WHERE id = ?",
                (project_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "description": row["description"],
                "project_type": row["project_type"],
                "provider": row["provider"],
                "model": row["model"],
                "status": row["status"],
                "with_tests": bool(row["with_tests"]),
                "validate": bool(row["validate"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "completed_at": row["completed_at"],
                "log_file": row["log_file"],
                "artifact_path": row["artifact_path"],
                "error_message": row["error_message"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
    
    def list_projects(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all projects with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM projects"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "description": row["description"],
                    "project_type": row["project_type"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "status": row["status"],
                    "with_tests": bool(row["with_tests"]),
                    "validate": bool(row["validate"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "completed_at": row["completed_at"],
                    "artifact_path": row["artifact_path"],
                    "error_message": row["error_message"]
                }
                for row in rows
            ]
    
    def update_status(
        self,
        project_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update project status"""
        with sqlite3.connect(self.db_path) as conn:
            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [status]
            
            if status in [ProjectStatus.DONE, ProjectStatus.FAILED]:
                updates.append("completed_at = CURRENT_TIMESTAMP")
            
            if error_message:
                updates.append("error_message = ?")
                params.append(error_message)
            
            params.append(project_id)
            
            conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
    
    def update_log_file(self, project_id: str, log_file: str):
        """Update log file path"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE projects SET log_file = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (log_file, project_id)
            )
            conn.commit()
    
    def update_artifact_path(self, project_id: str, artifact_path: str):
        """Update artifact path"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE projects SET artifact_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (artifact_path, project_id)
            )
            conn.commit()
    
    def delete_project(self, project_id: str):
        """Delete a project"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
