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
    """SQLite database for storing project runs and chat history"""
    
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
            
            # Chat history table for persistent memory
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Index for faster chat history lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_history_project 
                ON chat_history(project_id)
            """)
            
            conn.commit()
    
    # ==================== Chat History Methods ====================
    
    def add_chat_message(
        self,
        project_id: str,
        role: str,
        content: str
    ) -> int:
        """Add a chat message to history. Returns message ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_history (project_id, role, content)
                VALUES (?, ?, ?)
                """,
                (project_id, role, content)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_chat_history(
        self,
        project_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get chat history for a project, ordered by creation time."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, role, content, created_at 
                FROM chat_history 
                WHERE project_id = ? 
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (project_id, limit)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
    
    def clear_chat_history(self, project_id: str):
        """Clear all chat history for a project."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM chat_history WHERE project_id = ?",
                (project_id,)
            )
            conn.commit()
    
    def get_recent_context(
        self,
        project_id: str,
        max_messages: int = 20
    ) -> str:
        """Get recent chat as formatted context string for AI."""
        history = self.get_chat_history(project_id, limit=max_messages)
        if not history:
            return ""
        
        context_parts = []
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role_label}: {msg['content']}")
        
        return "\n\n".join(context_parts)
    
    # ==================== Project Methods ====================
    
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
                "validate_code": bool(row["validate"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "completed_at": row["completed_at"],
                "log_file": row["log_file"],
                "artifact_path": row["artifact_path"],
                "error_message": row["error_message"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
    
    def get_project_by_path(self, artifact_path: str) -> Optional[Dict[str, Any]]:
        """Get project by artifact path (for resume functionality)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM projects WHERE artifact_path = ?",
                (artifact_path,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self.get_project(row["id"])
    
    def update_project_model(self, project_id: str, provider: str, model: str):
        """Update project's AI provider and model"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE projects 
                SET provider = ?, model = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (provider, model, project_id)
            )
            conn.commit()
    
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
                    "validate_code": bool(row["validate"]),
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
            
            if error_message is not None:
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
        """Delete a project and its chat history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chat_history WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

