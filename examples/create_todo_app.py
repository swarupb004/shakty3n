"""
Example: Creating a Todo List Web App
"""
from shakty3n import (
    AIProviderFactory,
    AutonomousExecutor,
    load_env_vars
)

# Load environment variables
load_env_vars()

# Create AI provider (OpenAI GPT-4)
ai_provider = AIProviderFactory.create_provider(
    provider_name="openai",
    api_key=None,  # Will use OPENAI_API_KEY from .env
    model="gpt-4"
)

# Create autonomous executor
executor = AutonomousExecutor(
    ai_provider=ai_provider,
    output_dir="./examples/todo_app"
)

# Project description
description = """
A modern todo list application with the following features:
- User authentication (sign up, login, logout)
- Create, read, update, delete todos
- Mark todos as complete/incomplete
- Filter by status (all, active, completed)
- Categorize todos with tags
- Set due dates and priorities
- Responsive design for mobile and desktop
- Dark mode support
"""

# Execute project
print("Starting autonomous project creation...")
result = executor.execute_project(
    description=description,
    project_type="web-react",
    requirements={
        "framework": "react",
        "styling": "tailwindcss",
        "state_management": "react-hooks",
        "routing": "react-router",
        "backend": "firebase"
    }
)

# Print results
if result["success"]:
    print("\n✓ Todo app created successfully!")
    print(f"Location: {result['generation']['output_dir']}")
    print(f"Files created: {len(result['generation'].get('files', []))}")
    
    print("\nTo run the app:")
    print("1. cd", result['generation']['output_dir'])
    print("2. npm install")
    print("3. npm start")
else:
    print("\n✗ Project creation failed")
    print(f"Error: {result.get('error', 'Unknown error')}")
