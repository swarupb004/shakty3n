"""
Tests for the Project Orchestration API
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from platform_api.database import ProjectDatabase, ProjectStatus
from platform_api.projects import init_project_api
from shakty3n import Config


@pytest.fixture
def test_db():
    """Create a test database"""
    import tempfile
    db_path = os.path.join(tempfile.gettempdir(), "test_shakty3n.db")
    # Remove existing test db
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = ProjectDatabase(db_path)
    yield db
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def api_client(test_db):
    """Create test client with database"""
    from platform_api.main import app
    
    # Initialize config
    config = Config()
    
    # Initialize project API with test database
    init_project_api(test_db, config)
    
    client = TestClient(app)
    yield client


def test_health_endpoint(api_client):
    """Test health check endpoint"""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_project(api_client):
    """Test creating a new project"""
    project_data = {
        "description": "Test todo app",
        "project_type": "web-react",
        "provider": "openai",
        "model": "gpt-4",
        "with_tests": True,
        "validate_code": False
    }
    
    response = api_client.post("/api/projects", json=project_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["description"] == project_data["description"]
    assert data["project_type"] == project_data["project_type"]
    assert data["status"] == ProjectStatus.PLANNING


def test_list_projects(api_client, test_db):
    """Test listing projects"""
    # Create a test project directly in database
    test_db.create_project(
        project_id="test123",
        description="Test project",
        project_type="web-react",
        provider="openai",
        model="gpt-4"
    )
    
    response = api_client.get("/api/projects")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["id"] == "test123"


def test_get_project(api_client, test_db):
    """Test getting a specific project"""
    # Create a test project
    test_db.create_project(
        project_id="test456",
        description="Another test project",
        project_type="web-vue",
        provider="anthropic"
    )
    
    response = api_client.get("/api/projects/test456")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == "test456"
    assert data["description"] == "Another test project"


def test_get_nonexistent_project(api_client):
    """Test getting a project that doesn't exist"""
    response = api_client.get("/api/projects/nonexistent")
    assert response.status_code == 404


def test_delete_project(api_client, test_db):
    """Test deleting a project"""
    # Create a test project
    test_db.create_project(
        project_id="test789",
        description="Project to delete",
        project_type="android",
        provider="google"
    )
    
    # Delete it
    response = api_client.delete("/api/projects/test789")
    assert response.status_code == 200
    
    # Verify it's deleted
    assert test_db.get_project("test789") is None


def test_database_create_project(test_db):
    """Test database project creation"""
    project = test_db.create_project(
        project_id="db_test_1",
        description="Database test",
        project_type="ios",
        provider="openai",
        model="gpt-4",
        with_tests=True,
        validate=True
    )
    
    assert project["id"] == "db_test_1"
    assert project["status"] == ProjectStatus.PLANNING
    assert project["with_tests"] is True
    assert project["validate_code"] is True


def test_database_update_status(test_db):
    """Test updating project status"""
    test_db.create_project(
        project_id="db_test_2",
        description="Status test",
        project_type="flutter",
        provider="ollama"
    )
    
    # Update status
    test_db.update_status("db_test_2", ProjectStatus.GENERATING)
    
    project = test_db.get_project("db_test_2")
    assert project["status"] == ProjectStatus.GENERATING


def test_database_update_artifact_path(test_db):
    """Test updating artifact path"""
    test_db.create_project(
        project_id="db_test_3",
        description="Artifact test",
        project_type="desktop-electron",
        provider="anthropic"
    )
    
    # Update artifact path
    test_db.update_artifact_path("db_test_3", "/path/to/artifact")
    
    project = test_db.get_project("db_test_3")
    assert project["artifact_path"] == "/path/to/artifact"


def test_database_list_projects(test_db):
    """Test listing projects with filters"""
    # Create multiple projects
    test_db.create_project(
        project_id="list_test_1",
        description="List test 1",
        project_type="web-react",
        provider="openai"
    )
    test_db.update_status("list_test_1", ProjectStatus.DONE)
    
    test_db.create_project(
        project_id="list_test_2",
        description="List test 2",
        project_type="web-vue",
        provider="anthropic"
    )
    test_db.update_status("list_test_2", ProjectStatus.FAILED)
    
    test_db.create_project(
        project_id="list_test_3",
        description="List test 3",
        project_type="android",
        provider="google"
    )
    
    # List all
    all_projects = test_db.list_projects()
    assert len(all_projects) >= 3
    
    # List only done
    done_projects = test_db.list_projects(status=ProjectStatus.DONE)
    assert len(done_projects) >= 1
    assert all(p["status"] == ProjectStatus.DONE for p in done_projects)
    
    # List only failed
    failed_projects = test_db.list_projects(status=ProjectStatus.FAILED)
    assert len(failed_projects) >= 1
    assert all(p["status"] == ProjectStatus.FAILED for p in failed_projects)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
