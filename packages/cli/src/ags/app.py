"""AgSense CLI application with Typer."""

import os
import sys
from pathlib import Path

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

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
        console.print("[bold blue]AgSense CLI[/bold blue] v0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
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
                console.print("[red]❌ Dependency sync failed:[/red]")
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
                console.print("[yellow]⚠️  Pre-commit hooks installation failed:[/yellow]")
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
                console.print("\n[red]Test failures:[/red]")
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
        "Validating MCP adapter compliance, schema, and env flags...",
        border_style="blue"
    ))

    # Check MCP feature flag
    mcp_enabled = os.getenv("AGS_MCP_ENABLED", "false").lower() in ("true", "1", "yes")
    console.print(f"\n[bold]Environment Flag:[/bold] AGS_MCP_ENABLED={'✅ Enabled' if mcp_enabled else '❌ Disabled'}")

    # Define agent packages
    agent_packages = [
        "agent-ingest",
        "agent-retrieval",
        "agent-scoring",
        "agent-notify",
        "agent-billing"
    ]

    # Create readiness table
    table = Table(title="Agent MCP Readiness Status", show_lines=True)
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Detected Stub", justify="center")
    table.add_column("Protocol Compliance", justify="center")
    table.add_column("Schema Validation", justify="center")
    table.add_column("Env Flag", justify="center")

    project_root = Path.cwd()
    packages_dir = project_root / "packages"

    all_ready = True

    for agent_name in agent_packages:
        agent_path = packages_dir / agent_name
        mcp_adapter_path = agent_path / "adapters" / "mcp_stub.py"

        detected_stub = "❌"
        protocol_compliance = "❌"
        schema_validation = "❌"

        if agent_path.exists():
            if mcp_adapter_path.exists():
                try:
                    content = mcp_adapter_path.read_text()

                    # Check if stub is detected
                    if "class" in content and "MCPStub" in content:
                        detected_stub = "✅"

                    # Check protocol compliance (has _process_request method)
                    if "_process_request" in content and "async def" in content:
                        protocol_compliance = "✅"

                    # Check schema validation (uses AgentInput/AgentOutput)
                    if "AgentInput" in content and "AgentOutput" in content:
                        schema_validation = "✅"

                    if detected_stub == "❌" or protocol_compliance == "❌" or schema_validation == "❌":
                        all_ready = False

                except Exception as e:
                    logger.error(f"Error checking {agent_name}: {e}")
                    all_ready = False
            else:
                all_ready = False
        else:
            all_ready = False

        env_flag_status = "✅" if mcp_enabled else "⚠️"
        table.add_row(
            agent_name,
            detected_stub,
            protocol_compliance,
            schema_validation,
            env_flag_status
        )

    console.print(table)

    # Summary
    total_agents = len(agent_packages)

    if all_ready and mcp_enabled:
        console.print(f"\n[green]🎉 All {total_agents} agents are fully MCP-ready![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  • Run [bold cyan]ags agent run all --trace[/bold cyan] to test orchestration")
        console.print("  • Check logs for proper request ID, latency metrics")
    elif all_ready and not mcp_enabled:
        console.print("\n[yellow]⚠️  All adapters are ready, but MCP is disabled[/yellow]")
        console.print("\nTo enable MCP mode, run:")
        console.print("  [bold cyan]export AGS_MCP_ENABLED=true[/bold cyan]")
    else:
        console.print("\n[red]❌ Some agents are not MCP-ready[/red]")
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
            import rich
            import typer
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

    import platform
    import sys

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


# Create a subcommand group for agent operations
agent_app = typer.Typer(name="agent", help="Agent management commands")
app.add_typer(agent_app, name="agent")


@agent_app.command("run")
def agent_run(
    target: str = typer.Argument(..., help="Target agent or 'all' for all agents"),
    trace: bool = typer.Option(False, "--trace", help="Enable request flow tracing"),
) -> None:
    """Run agent orchestrator simulation with optional tracing."""
    console.print(Panel.fit(
        "[bold blue]AgSense Agent Orchestrator Simulation[/bold blue]\n"
        f"Running: {target}",
        border_style="blue"
    ))

    # Check MCP mode
    mcp_enabled = os.getenv("AGS_MCP_ENABLED", "false").lower() in ("true", "1", "yes")
    console.print(f"\n[bold]MCP Mode:[/bold] {'✅ Enabled' if mcp_enabled else '❌ Disabled (using local adapters)'}")

    if not mcp_enabled:
        console.print("[yellow]💡 Tip: Enable MCP mode with 'export AGS_MCP_ENABLED=true'[/yellow]\n")

    # Run the simulation
    import asyncio
    try:
        asyncio.run(_run_agent_simulation(target, trace))
    except Exception as e:
        console.print(f"[red]❌ Simulation failed: {e}[/red]")
        logger.error(f"Agent simulation error: {e}", exc_info=True)
        raise typer.Exit(1)


async def _run_agent_simulation(target: str, trace: bool) -> None:
    """Run the actual agent simulation."""
    import time
    import uuid

    from rich.tree import Tree

    # Agent types to test
    if target == "all":
        agents_to_test = [
            "agent-ingest",
            "agent-retrieval",
            "agent-scoring",
            "agent-notify",
            "agent-billing"
        ]
    else:
        agents_to_test = [target]

    # Create test requests
    console.print(f"\n[bold]Testing {len(agents_to_test)} agent(s)...[/bold]\n")

    # Import adapters dynamically
    sys.path.insert(0, str(Path.cwd() / "packages"))

    mcp_enabled = os.getenv("AGS_MCP_ENABLED", "false").lower() in ("true", "1", "yes")

    results = []
    trace_tree = Tree("🔄 [bold cyan]Request Flow Trace[/bold cyan]") if trace else None

    for agent_type in agents_to_test:
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        correlation_id = f"corr_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        try:
            # Create agent-specific test payload
            if agent_type == "agent-ingest":
                payload = {"data": "test_data", "source": "cli_simulation"}
            elif agent_type == "agent-retrieval":
                payload = {"query": {"term": "test"}, "limit": 10}
            elif agent_type == "agent-scoring":
                payload = {"data": "test_item", "model": "default"}
            elif agent_type == "agent-notify":
                payload = {"recipient": "admin@test.com", "channel": "email", "message": "Test"}
            elif agent_type == "agent-billing":
                payload = {"amount": 100.0, "currency": "USD", "customer_id": "cust_123"}
            else:
                payload = {"test": "data"}

            # Import and create adapter if MCP is enabled
            if mcp_enabled:
                try:
                    # Import the MCP stub for this agent
                    if agent_type == "agent-ingest":
                        from agent_ingest.adapters.mcp_stub import IngestMCPStub
                        adapter = IngestMCPStub()
                    elif agent_type == "agent-retrieval":
                        from agent_retrieval.adapters.mcp_stub import RetrievalMCPStub
                        adapter = RetrievalMCPStub()
                    elif agent_type == "agent-scoring":
                        from agent_scoring.adapters.mcp_stub import ScoringMCPStub
                        adapter = ScoringMCPStub()
                    elif agent_type == "agent-notify":
                        from agent_notify.adapters.mcp_stub import NotifyMCPStub
                        adapter = NotifyMCPStub()
                    elif agent_type == "agent-billing":
                        from agent_billing.adapters.mcp_stub import BillingMCPStub
                        adapter = BillingMCPStub()
                    else:
                        raise ImportError(f"Unknown agent type: {agent_type}")

                    # Import contracts
                    from core.models.contracts import AgentInput, Priority

                    # Create request
                    agent_input = AgentInput(
                        request_id=request_id,
                        agent_type=agent_type,
                        payload=payload,
                        priority=Priority.NORMAL,
                        correlation_id=correlation_id
                    )

                    # Send request through MCP adapter
                    result = await adapter.send_request(agent_input)

                    latency_ms = (time.time() - start_time) * 1000

                    # Log structured output
                    logger.info(
                        "Agent request completed",
                        ts=time.time(),
                        agent=agent_type,
                        request_id=request_id,
                        latency_ms=round(latency_ms, 2),
                        status="ok" if result.status == "completed" else "error",
                        message=f"Processed by {agent_type}"
                    )

                    results.append({
                        "agent": agent_type,
                        "request_id": request_id,
                        "status": result.status,
                        "latency_ms": round(latency_ms, 2)
                    })

                    # Add to trace tree
                    if trace and trace_tree:
                        agent_node = trace_tree.add(f"[cyan]{agent_type}[/cyan]")
                        agent_node.add(f"[dim]Request ID:[/dim] {request_id}")
                        agent_node.add(f"[dim]Status:[/dim] [green]{result.status}[/green]")
                        agent_node.add(f"[dim]Latency:[/dim] {round(latency_ms, 2)}ms")
                        agent_node.add(f"[dim]Correlation ID:[/dim] {correlation_id}")

                except ImportError as e:
                    console.print(f"[yellow]⚠️  {agent_type}: Adapter not found (skipping)[/yellow]")
                    logger.warning(f"Could not import {agent_type}: {e}")
                    results.append({
                        "agent": agent_type,
                        "request_id": request_id,
                        "status": "skipped",
                        "latency_ms": 0
                    })
            else:
                # Simulate without MCP adapters
                import asyncio
                await asyncio.sleep(0.1)
                latency_ms = (time.time() - start_time) * 1000

                logger.info(
                    "Agent request completed (local mode)",
                    ts=time.time(),
                    agent=agent_type,
                    request_id=request_id,
                    latency_ms=round(latency_ms, 2),
                    status="ok",
                    message=f"Processed by {agent_type} (local)"
                )

                results.append({
                    "agent": agent_type,
                    "request_id": request_id,
                    "status": "completed",
                    "latency_ms": round(latency_ms, 2)
                })

                if trace and trace_tree:
                    agent_node = trace_tree.add(f"[cyan]{agent_type}[/cyan] (local mode)")
                    agent_node.add(f"[dim]Request ID:[/dim] {request_id}")
                    agent_node.add("[dim]Status:[/dim] [green]completed[/green]")
                    agent_node.add(f"[dim]Latency:[/dim] {round(latency_ms, 2)}ms")

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                "Agent request failed",
                ts=time.time(),
                agent=agent_type,
                request_id=request_id,
                latency_ms=round(latency_ms, 2),
                status="error",
                error=str(e)
            )
            results.append({
                "agent": agent_type,
                "request_id": request_id,
                "status": "error",
                "latency_ms": round(latency_ms, 2)
            })

            if trace and trace_tree:
                agent_node = trace_tree.add(f"[red]{agent_type}[/red]")
                agent_node.add(f"[dim]Request ID:[/dim] {request_id}")
                agent_node.add("[dim]Status:[/dim] [red]error[/red]")
                agent_node.add(f"[dim]Error:[/dim] {str(e)}")

    # Print trace tree if enabled
    if trace and trace_tree:
        console.print("\n")
        console.print(trace_tree)

    # Print results table
    results_table = Table(title="\n📊 Agent Execution Results", show_lines=True)
    results_table.add_column("Agent", style="cyan")
    results_table.add_column("Request ID", style="dim")
    results_table.add_column("Status", justify="center")
    results_table.add_column("Latency (ms)", justify="right")

    for result in results:
        status_display = (
            "[green]✅ " + result["status"] + "[/green]" if result["status"] == "completed"
            else "[red]❌ " + result["status"] + "[/red]"
        )
        results_table.add_row(
            result["agent"],
            result["request_id"],
            status_display,
            str(result["latency_ms"])
        )

    console.print(results_table)

    # Summary
    total = len(results)
    successful = sum(1 for r in results if r["status"] == "completed")
    avg_latency = sum(r["latency_ms"] for r in results) / total if total > 0 else 0

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  • Total agents tested: {total}")
    console.print(f"  • Successful: [green]{successful}[/green]")
    console.print(f"  • Failed: [red]{total - successful}[/red]")
    console.print(f"  • Average latency: {round(avg_latency, 2)}ms")

    if successful == total:
        console.print("\n[green]🎉 All agents executed successfully![/green]")
    else:
        console.print("\n[yellow]⚠️  Some agents failed execution[/yellow]")


if __name__ == "__main__":
    app()
