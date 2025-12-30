#!/usr/bin/env python3
"""
Shakty3n - Autonomous Agentic Coder CLI
"""
import click
import os
import subprocess
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shakty3n import (
    AIProviderFactory,
    AutonomousExecutor,
    Config,
    VirtualEnvManager,
    load_env_vars
)
from shakty3n.utils import validate_project_type

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Shakty3n - Autonomous Agentic Coder
    
    Build Web, Android, iOS, and Desktop applications autonomously
    with AI-powered planning, coding, and debugging.
    """
    pass


@cli.command()
@click.option('--description', '-d', help='Project description')
@click.option('--type', '-t', 'project_type', help='Project type (web/android/ios/desktop)')
@click.option('--provider', '-p', help='AI provider (openai/anthropic/google/ollama)')
@click.option('--model', '-m', help='AI model to use')
@click.option('--output', '-o', help='Output directory', default='./generated_projects')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--with-tests', is_flag=True, help='Generate tests for the project')
@click.option('--validate', is_flag=True, help='Validate the generated code')
def create(description, project_type, provider, model, output, interactive, with_tests, validate):
    """Create a new project autonomously"""
    
    # Load environment variables
    load_env_vars()
    config = Config()
    
    # Interactive mode
    if interactive or not (description and project_type):
        console.print(Panel.fit(
            "[bold cyan]Shakty3n - Autonomous Agentic Coder[/bold cyan]\n"
            "Let's create your application!",
            border_style="cyan"
        ))
        
        if not description:
            description = Prompt.ask("\n[bold]What do you want to build?[/bold]")
        
        if not project_type:
            console.print("\n[bold]Select project type:[/bold]")
            console.print("1. Web Application (React)")
            console.print("2. Web Application (Vue)")
            console.print("3. Web Application (Angular)")
            console.print("4. Web Application (Svelte)")
            console.print("5. Web Application (Next.js)")
            console.print("6. Mobile Application (Android)")
            console.print("7. Mobile Application (iOS)")
            console.print("8. Mobile Application (Flutter - Cross-platform)")
            console.print("9. Desktop Application (Electron)")
            console.print("10. Desktop Application (Python)")
            
            choice = Prompt.ask("Enter choice", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
            project_types = {
                "1": "web-react",
                "2": "web-vue",
                "3": "web-angular",
                "4": "web-svelte",
                "5": "web-nextjs",
                "6": "android",
                "7": "ios",
                "8": "flutter",
                "9": "desktop-electron",
                "10": "desktop-python"
            }
            project_type = project_types[choice]
        
        if not provider:
            console.print("\n[bold]Select AI Provider:[/bold]")
            console.print("1. OpenAI (GPT-4)")
            console.print("2. Anthropic (Claude)")
            console.print("3. Google (Gemini)")
            console.print("4. Ollama (Local)")
            
            choice = Prompt.ask("Enter choice", choices=["1", "2", "3", "4"], default="1")
            providers = {
                "1": "openai",
                "2": "anthropic",
                "3": "google",
                "4": "ollama"
            }
            provider = providers[choice]
    
    # Validate inputs
    if not description:
        console.print("[red]Error: Project description is required[/red]")
        return
    
    if not project_type or not validate_project_type(project_type):
        console.print("[red]Error: Valid project type is required[/red]")
        return
    
    # Set defaults
    provider = provider or config.provider
    model = model or config.model
    
    # Get API key
    provider_config = config.get_provider_config(provider)
    api_key = provider_config.get("api_key")
    
    if not api_key and provider != "ollama":
        console.print(f"[yellow]Warning: No API key found for {provider}[/yellow]")
        console.print(f"Please set {provider.upper()}_API_KEY in your .env file")
        
        if not Confirm.ask("Continue anyway?", default=False):
            return
    
    # Create AI provider
    try:
        console.print(f"\n[cyan]Initializing {provider} ({model})...[/cyan]")
        ai_provider = AIProviderFactory.create_provider(provider, api_key, model)
    except Exception as e:
        console.print(f"[red]Error creating AI provider: {e}[/red]")
        return
    
    # Create executor
    executor = AutonomousExecutor(ai_provider, output)
    
    # Show summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]Project Configuration[/bold cyan]")
    console.print("="*60)
    console.print(f"[bold]Description:[/bold] {description}")
    console.print(f"[bold]Type:[/bold] {project_type}")
    console.print(f"[bold]AI Provider:[/bold] {provider} ({model})")
    console.print(f"[bold]Output:[/bold] {output}")
    console.print(f"[bold]Generate Tests:[/bold] {with_tests}")
    console.print(f"[bold]Validate Code:[/bold] {validate}")
    console.print("="*60 + "\n")
    
    if not Confirm.ask("Start autonomous execution?", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Execute project
    try:
        result = executor.execute_project(
            description=description,
            project_type=project_type,
            requirements={},
            generate_tests=with_tests,
            validate_code=validate
        )
        
        if result.get("success"):
            console.print("\n[bold green]✓ Project created successfully![/bold green]")
            if result.get("generation", {}).get("output_dir"):
                console.print(f"[bold]Location:[/bold] {result['generation']['output_dir']}")
        else:
            console.print("\n[bold red]✗ Project creation failed[/bold red]")
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
                
    except Exception as e:
        console.print(f"\n[bold red]✗ Execution error: {e}[/bold red]")


@cli.command()
def configure():
    """Configure API keys and settings"""
    
    console.print(Panel.fit(
        "[bold cyan]Shakty3n Configuration[/bold cyan]",
        border_style="cyan"
    ))
    
    env_file = ".env"
    env_example = ".env.example"
    
    # Read example if exists
    config_template = {}
    if os.path.exists(env_example):
        with open(env_example, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config_template[key] = value
    
    # Collect configuration
    console.print("\n[bold]Enter your configuration:[/bold]")
    console.print("(Press Enter to skip)\n")
    
    config_values = {}
    
    # API Keys
    openai_key = Prompt.ask("OpenAI API Key", default="", password=True)
    if openai_key:
        config_values["OPENAI_API_KEY"] = openai_key
    
    anthropic_key = Prompt.ask("Anthropic API Key", default="", password=True)
    if anthropic_key:
        config_values["ANTHROPIC_API_KEY"] = anthropic_key
    
    google_key = Prompt.ask("Google API Key", default="", password=True)
    if google_key:
        config_values["GOOGLE_API_KEY"] = google_key
    
    # Settings
    provider = Prompt.ask("Default AI Provider", 
                         choices=["openai", "anthropic", "google", "ollama"],
                         default="openai")
    config_values["DEFAULT_AI_PROVIDER"] = provider
    
    model = Prompt.ask("Default Model", default="gpt-4")
    config_values["DEFAULT_MODEL"] = model
    
    # Ollama Settings
    ollama_url = Prompt.ask("Ollama Base URL (for running in Docker use http://host.docker.internal:11434)", 
                           default="http://localhost:11434")
    config_values["OLLAMA_BASE_URL"] = ollama_url
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write("# Shakty3n Configuration\n\n")
        f.write("# AI Model API Keys\n")
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
            value = config_values.get(key, "")
            f.write(f"{key}={value}\n")
        
        f.write("\n# Default Settings\n")
        for key in ["DEFAULT_AI_PROVIDER", "DEFAULT_MODEL", "OLLAMA_BASE_URL"]:
            value = config_values.get(key, "")
            f.write(f"{key}={value}\n")
        
        f.write("\n# Application Settings\n")
        f.write("AUTO_DEBUG=true\n")
        f.write("MAX_RETRIES=3\n")
        f.write("VERBOSE=true\n")
    
    console.print(f"\n[green]✓ Configuration saved to {env_file}[/green]")


@cli.command()
@click.option('--provider', '-p', help='AI provider to test')
def test(provider):
    """Test AI provider connection"""
    
    load_env_vars()
    config = Config()
    
    provider = provider or config.provider
    provider_config = config.get_provider_config(provider)
    
    console.print(f"\n[cyan]Testing {provider} connection...[/cyan]")
    
    try:
        ai_provider = AIProviderFactory.create_provider(
            provider,
            provider_config.get("api_key"),
            provider_config.get("model")
        )
        
        # Test with simple prompt
        response = ai_provider.generate(
            "Say 'Hello from Shakty3n!' if you can read this.",
            temperature=0.3
        )
        
        console.print(f"[green]✓ Connection successful![/green]")
        console.print(f"[bold]Response:[/bold] {response[:100]}...")
        
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")


@cli.command()
@click.option('--env-dir', default='.shakty3n_venv', help='Virtual environment directory')
@click.option('--test-command', default='-m pytest tests/test_basic.py', help='Command to run inside the environment')
@click.option('--skip-install', is_flag=True, help='Skip installing dependencies into the environment')
def sandbox(env_dir, test_command, skip_install):
    """Create a virtual environment and run tests there"""
    console.print(Panel.fit(
        "[bold cyan]Shakty3n Sandbox[/bold cyan]\n\n"
        "Creates an isolated virtual environment and runs tests inside it.",
        border_style="cyan"
    ))

    manager = VirtualEnvManager(env_dir)

    try:
        console.print(f"\n[cyan]Creating virtual environment at {env_dir}...[/cyan]")
        manager.create()
        console.print(f"[green]✓ Virtual environment ready ({manager.python_path})[/green]")

        if not skip_install:
            if os.path.exists("requirements.txt"):
                console.print("[cyan]Installing requirements...[/cyan]")
                manager.install_requirements("requirements.txt")
            console.print("[cyan]Installing pytest...[/cyan]")
            manager.run_command(["-m", "pip", "install", "pytest"])
            console.print("[cyan]Installing shakty3n in editable mode...[/cyan]")
            manager.install_local_package(editable=True)
        else:
            console.print("[yellow]Skipping dependency installation[/yellow]")

        console.print("\n[cyan]Running tests inside the sandbox...[/cyan]")
        result = manager.run_command(test_command)
        if result.stdout:
            console.print(f"[bold]Output:[/bold]\n{result.stdout}")
        if result.stderr:
            console.print(f"[yellow]Warnings:[/yellow]\n{result.stderr}")
        console.print(f"[green]✓ Tests completed[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Sandbox run failed: {e}[/red]")
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        if stdout:
            console.print(f"[bold]Output:[/bold]\n{stdout}")
        if stderr:
            console.print(f"[red]Errors:[/red]\n{stderr}")
    except Exception as e:
        console.print(f"[red]✗ Sandbox run failed: {e}[/red]")


@cli.command()
def info():
    """Show information about Shakty3n"""
    
    console.print(Panel.fit(
        "[bold cyan]Shakty3n - Autonomous Agentic Coder[/bold cyan]\n\n"
        "[bold]Version:[/bold] 1.0.0\n"
        "[bold]Description:[/bold] Build applications autonomously with AI\n\n"
        "[bold]Supported Platforms:[/bold]\n"
        "  • Web (React, Vue, Angular)\n"
        "  • Android (Kotlin, Java)\n"
        "  • iOS (Swift)\n"
        "  • Desktop (Electron, Python)\n\n"
        "[bold]Supported AI Providers:[/bold]\n"
        "  • OpenAI (GPT-4, GPT-3.5)\n"
        "  • Anthropic (Claude)\n"
        "  • Google (Gemini)\n"
        "  • Ollama (Local Models)\n\n"
        "[bold]Features:[/bold]\n"
        "  • Autonomous planning and execution\n"
        "  • Multi-platform code generation\n"
        "  • Automatic debugging and fixing\n"
        "  • Progress tracking and reporting",
        border_style="cyan"
    ))


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host, port, reload):
    """Start the Shakty3n API server"""
    
    console.print(Panel.fit(
        "[bold cyan]Shakty3n API Server[/bold cyan]\n\n"
        "Starting FastAPI server for project orchestration...",
        border_style="cyan"
    ))
    
    # Check if platform_api exists
    api_dir = os.path.join(os.path.dirname(__file__), 'platform_api')
    if not os.path.exists(api_dir):
        console.print("[red]Error: platform_api directory not found[/red]")
        return
    
    console.print(f"\n[cyan]Server will start at:[/cyan] http://{host}:{port}")
    console.print(f"[cyan]API documentation:[/cyan] http://{host}:{port}/docs")
    console.print(f"[cyan]Health check:[/cyan] http://{host}:{port}/health\n")
    
    try:
        import uvicorn
        uvicorn.run(
            "platform_api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except ImportError:
        console.print("[red]Error: uvicorn not installed[/red]")
        console.print("Install with: pip install uvicorn")
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")


if __name__ == "__main__":
    cli()
