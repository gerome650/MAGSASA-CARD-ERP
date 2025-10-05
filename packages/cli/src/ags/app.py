"""AgSense CLI application with Typer."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
console = Console()
app = typer.Typer(
    name="ags",
    help="AgSense CLI - Intelligent Agent Orchestration Platform",
    add_completion=False,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]AgSense CLI[/bold blue] v0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, 
        "--version", 
        "-v", 
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False, 
        "--verbose", 
        "-V", 
        help="Enable verbose logging"
    ),
) -> None:
    """AgSense CLI - Intelligent Agent Orchestration Platform."""
    if verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer()  # Pretty console output for verbose mode
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    logger.info("AgSense CLI started", verbose=verbose)


@app.command()
def dev_setup() -> None:
    """Set up development environment and verify installation."""
    console.print(Panel.fit(
        "[bold blue]AgSense Development Setup[/bold blue]\n"
        "Setting up development environment...",
        border_style="blue"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Check Python version
        task1 = progress.add_task("Checking Python version...", total=None)
        python_version = sys.version_info
        if python_version < (3, 10):
            console.print("[red]❌ Python 3.10+ required[/red]")
            raise typer.Exit(1)
        progress.update(task1, description="✅ Python version OK")
        
        # Check uv installation
        task2 = progress.add_task("Checking uv installation...", total=None)
        try:
            import subprocess
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise FileNotFoundError("uv not found")
            progress.update(task2, description="✅ uv installed")
        except (FileNotFoundError, subprocess.SubprocessError):
            console.print("[red]❌ uv not found. Please install uv first:[/red]")
            console.print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
            raise typer.Exit(1)
        
        # Check project structure
        task3 = progress.add_task("Checking project structure...", total=None)
        project_root = Path.cwd()
        required_dirs = ["packages", "tests", ".github"]
        missing_dirs = [d for d in required_dirs if not (project_root / d).exists()]
        if missing_dirs:
            console.print(f"[red]❌ Missing directories: {', '.join(missing_dirs)}[/red]")
            raise typer.Exit(1)
        progress.update(task3, description="✅ Project structure OK")
        
        # Check dependencies
        task4 = progress.add_task("Checking dependencies...", total=None)
        try:
            result = subprocess.run(
                ["uv", "sync", "--dev"], 
                capture_output=True, 
                text=True,
                cwd=project_root
            )
            if result.returncode != 0:
                console.print(f"[red]❌ Dependency sync failed:[/red]")
                console.print(result.stderr)
                raise typer.Exit(1)
            progress.update(task4, description="✅ Dependencies synced")
        except subprocess.SubprocessError as e:
            console.print(f"[red]❌ Failed to sync dependencies: {e}[/red]")
            raise typer.Exit(1)
        
        # Install pre-commit hooks
        task5 = progress.add_task("Installing pre-commit hooks...", total=None)
        try:
            result = subprocess.run(
                ["pre-commit", "install"], 
                capture_output=True, 
                text=True,
                cwd=project_root
            )
            if result.returncode != 0:
                console.print(f"[yellow]⚠️  Pre-commit hooks installation failed:[/yellow]")
                console.print(result.stderr)
            else:
                progress.update(task5, description="✅ Pre-commit hooks installed")
        except subprocess.SubprocessError:
            console.print("[yellow]⚠️  Pre-commit not available[/yellow]")
            progress.update(task5, description="⚠️  Pre-commit skipped")
    
    console.print("\n[green]🎉 Development environment setup complete![/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  • Run [bold]ags test[/bold] to verify everything works")
    console.print("  • Run [bold]ags mcp-check[/bold] to check agent readiness")
    console.print("  • Run [bold]make run[/bold] to start all agents")


@app.command()
def test() -> None:
    """Run tests and verify the installation."""
    console.print(Panel.fit(
        "[bold blue]AgSense Test Suite[/bold blue]\n"
        "Running tests to verify installation...",
        border_style="blue"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Run pytest
        task1 = progress.add_task("Running tests...", total=None)
        try:
            import subprocess
            result = subprocess.run(
                ["uv", "run", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                progress.update(task1, description="✅ All tests passed")
                console.print(f"\n[green]{result.stdout}[/green]")
            else:
                progress.update(task1, description="❌ Some tests failed")
                console.print(f"\n[red]Test failures:[/red]")
                console.print(result.stdout)
                console.print(result.stderr)
                raise typer.Exit(1)
                
        except subprocess.SubprocessError as e:
            console.print(f"[red]❌ Failed to run tests: {e}[/red]")
            raise typer.Exit(1)
    
    console.print("\n[green]🎉 All tests passed![/green]")


@app.command()
def mcp_check() -> None:
    """Check MCP (Model Context Protocol) readiness across all agents."""
    console.print(Panel.fit(
        "[bold blue]AgSense MCP Readiness Check[/bold blue]\n"
        "Checking agent MCP adapter readiness...",
        border_style="blue"
    ))
    
    # Define agent packages
    agent_packages = [
        "agent-orchestrator",
        "agent-ingest", 
        "agent-retrieval",
        "agent-scoring",
        "agent-notify",
        "agent-billing"
    ]
    
    # Create readiness table
    table = Table(title="Agent MCP Readiness Status")
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("MCP Adapter", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Notes", style="dim")
    
    project_root = Path.cwd()
    packages_dir = project_root / "packages"
    
    for agent_name in agent_packages:
        agent_path = packages_dir / agent_name
        mcp_adapter_path = agent_path / "adapters" / "mcp_stub.py"
        
        if agent_path.exists():
            if mcp_adapter_path.exists():
                # Try to import and validate the MCP adapter
                try:
                    # Simple file check for now - could be enhanced with actual import
                    content = mcp_adapter_path.read_text()
                    if "class" in content and "def" in content:
                        status = "✅ Ready"
                        notes = "MCP adapter found"
                    else:
                        status = "⚠️  Incomplete"
                        notes = "MCP adapter exists but incomplete"
                except Exception:
                    status = "❌ Error"
                    notes = "MCP adapter file error"
            else:
                status = "❌ Missing"
                notes = "No MCP adapter found"
        else:
            status = "❌ Missing"
            notes = "Agent package not found"
        
        table.add_row(agent_name, "mcp_stub.py", status, notes)
    
    console.print(table)
    
    # Summary
    total_agents = len(agent_packages)
    ready_count = sum(1 for row in table.rows if "✅" in str(row.cells[2]))
    
    if ready_count == total_agents:
        console.print(f"\n[green]🎉 All {total_agents} agents are MCP-ready![/green]")
    else:
        console.print(f"\n[yellow]⚠️  {ready_count}/{total_agents} agents are MCP-ready[/yellow]")
        console.print("Run [bold]make setup[/bold] to complete the setup")


@app.command()
def health_check() -> None:
    """Check system health and agent status."""
    console.print(Panel.fit(
        "[bold blue]AgSense Health Check[/bold blue]\n"
        "Checking system and agent health...",
        border_style="blue"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Check Python environment
        task1 = progress.add_task("Checking Python environment...", total=None)
        try:
            import sys
            python_version = sys.version_info
            if python_version >= (3, 10):
                progress.update(task1, description="✅ Python environment OK")
            else:
                progress.update(task1, description="❌ Python version too old")
                raise typer.Exit(1)
        except Exception:
            progress.update(task1, description="❌ Python environment error")
            raise typer.Exit(1)
        
        # Check dependencies
        task2 = progress.add_task("Checking dependencies...", total=None)
        try:
            import pydantic
            import typer
            import rich
            progress.update(task2, description="✅ Core dependencies OK")
        except ImportError as e:
            progress.update(task2, description=f"❌ Missing dependency: {e}")
            raise typer.Exit(1)
        
        # Check project structure
        task3 = progress.add_task("Checking project structure...", total=None)
        project_root = Path.cwd()
        required_files = ["pyproject.toml", "Makefile", ".pre-commit-config.yaml"]
        missing_files = [f for f in required_files if not (project_root / f).exists()]
        if missing_files:
            progress.update(task3, description=f"❌ Missing files: {', '.join(missing_files)}")
            raise typer.Exit(1)
        else:
            progress.update(task3, description="✅ Project structure OK")
    
    console.print("\n[green]🎉 System health check passed![/green]")


@app.command()
def info() -> None:
    """Show system information and configuration."""
    console.print(Panel.fit(
        "[bold blue]AgSense System Information[/bold blue]",
        border_style="blue"
    ))
    
    # System info table
    info_table = Table(show_header=False, box=None)
    info_table.add_column("Property", style="cyan", no_wrap=True)
    info_table.add_column("Value", style="white")
    
    import sys
    import platform
    
    info_table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    info_table.add_row("Platform", f"{platform.system()} {platform.release()}")
    info_table.add_row("Architecture", platform.machine())
    info_table.add_row("Working Directory", str(Path.cwd()))
    info_table.add_row("CLI Version", "0.1.0")
    
    console.print(info_table)
    
    # Environment variables
    env_vars = ["PATH", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV"]
    env_table = Table(title="Environment Variables")
    env_table.add_column("Variable", style="cyan")
    env_table.add_column("Value", style="dim")
    
    for var in env_vars:
        value = os.getenv(var, "Not set")
        if len(value) > 50:
            value = value[:47] + "..."
        env_table.add_row(var, value)
    
    console.print(env_table)


if __name__ == "__main__":
    app()
