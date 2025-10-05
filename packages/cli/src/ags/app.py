"""AgSense CLI application with Typer.

This module provides a comprehensive CLI interface for the AgSense platform,
including development setup, testing, MCP validation, health checks, and
agent orchestration capabilities.

Enterprise-grade features:
- Comprehensive error handling with proper exit codes
- Structured logging with multiple output formats
- Rich terminal UI with progress indicators and tables
- MCP (Model Context Protocol) adapter validation
- Agent orchestration and simulation capabilities
"""

import asyncio
import importlib.util
import logging
import os
import platform
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

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
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Global variables
logger = structlog.get_logger(__name__)
console = Console()
app = typer.Typer(
    name="ags",
    help="AgSense CLI - Intelligent Agent Orchestration Platform",
    add_completion=False,
    rich_markup_mode="rich",
)

# Global state for CLI options (managed via context)
_quiet_mode = False

# Constants
CLI_VERSION = "0.1.0"  # Centralized version string
REQUIRED_PYTHON_VERSION = (3, 10)
REQUIRED_DIRECTORIES = ["packages", "tests", ".github"]
REQUIRED_FILES = ["pyproject.toml", "Makefile", ".pre-commit-config.yaml"]
AGENT_PACKAGES = [
    "agent-ingest",
    "agent-retrieval",
    "agent-scoring",
    "agent-notify",
    "agent-billing",
]


def _console_print(message: str, force: bool = False) -> None:
    """Print to console respecting quiet mode.

    Args:
        message: The message to print (supports Rich markup)
        force: If True, print even in quiet mode (for errors/critical info)
    """
    if force or not _quiet_mode:
        console.print(message)


def version_callback(value: bool) -> None:
    """Print version and exit.

    Args:
        value: If True, print version information and exit

    Raises:
        typer.Exit: Always exits after printing version
    """
    if value:
        console.print(f"[bold blue]AgSense CLI[/bold blue] v{CLI_VERSION}")
        raise typer.Exit()


def _check_python_version() -> None:
    """Check if Python version meets minimum requirements.

    Validates that the current Python interpreter meets the minimum version
    requirement defined in REQUIRED_PYTHON_VERSION constant.

    Raises:
        typer.Exit: If Python version is insufficient or check fails
    """
    try:
        python_version = sys.version_info
        required_version_str = ".".join(map(str, REQUIRED_PYTHON_VERSION))
        current_version_str = f"{python_version.major}.{python_version.minor}"

        if python_version < REQUIRED_PYTHON_VERSION:
            console.print(
                f"[red]❌ Python {required_version_str}+ required, found {current_version_str}[/red]",
                style="bold",
            )
            console.print(
                f"   💡 [dim]Hint: Install Python {required_version_str} or higher and retry[/dim]"
            )
            logger.error(
                "Python version check failed",
                required=required_version_str,
                found=current_version_str,
            )
            raise typer.Exit(1)

        logger.debug("Python version check passed", version=current_version_str)

    except typer.Exit:
        raise  # Re-raise typer.Exit without wrapping
    except Exception as e:
        console.print(f"[red]❌ Failed to check Python version: {e}[/red]")
        logger.error("Python version check failed", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


def _check_uv_installation() -> None:
    """Check if uv package manager is installed and available.

    Verifies that the uv package manager (https://github.com/astral-sh/uv)
    is installed and functional by running 'uv --version'.

    Raises:
        typer.Exit: If uv is not found, fails to execute, or times out
    """
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,  # Don't raise on non-zero exit
        )
        if result.returncode != 0:
            raise FileNotFoundError("uv command failed")

        logger.debug("uv installation check passed", version=result.stdout.strip())

    except FileNotFoundError:
        console.print("[red]❌ uv package manager not found[/red]")
        console.print(
            "   💡 [bold]Install uv:[/bold] curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
        console.print("   💡 [dim]Or visit: https://github.com/astral-sh/uv[/dim]")
        logger.error("uv not found in PATH")
        raise typer.Exit(1) from None
    except subprocess.TimeoutExpired:
        console.print("[red]❌ uv command timed out (10 seconds)[/red]")
        console.print(
            "   💡 [dim]Hint: Check your uv installation and network connectivity[/dim]"
        )
        logger.error("uv installation check timed out")
        raise typer.Exit(1) from None
    except subprocess.SubprocessError as e:
        console.print(f"[red]❌ Failed to execute uv: {e}[/red]")
        logger.error("uv installation check failed", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


def _check_project_structure(project_root: Path) -> None:
    """Check if required project directories exist.

    Validates that all required directories defined in REQUIRED_DIRECTORIES
    are present in the project root. This ensures the CLI is being run from
    the correct project location.

    Args:
        project_root: Path to the project root directory

    Raises:
        typer.Exit: If any required directories are missing or check fails
    """
    try:
        missing_dirs = [
            d for d in REQUIRED_DIRECTORIES if not (project_root / d).exists()
        ]
        if missing_dirs:
            console.print(
                f"[red]❌ Missing required directories: {', '.join(missing_dirs)}[/red]"
            )
            console.print(
                "   💡 [dim]Hint: Ensure you're in the project root directory[/dim]"
            )
            console.print(f"   💡 [dim]Current directory: {project_root}[/dim]")
            logger.error(
                "Project structure check failed",
                missing_dirs=missing_dirs,
                project_root=str(project_root),
            )
            raise typer.Exit(1)

        logger.debug(
            "Project structure check passed",
            directories=REQUIRED_DIRECTORIES,
            project_root=str(project_root),
        )

    except typer.Exit:
        raise  # Re-raise typer.Exit without wrapping
    except Exception as e:
        console.print(f"[red]❌ Project structure check failed: {e}[/red]")
        logger.error("Project structure check failed", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


def _check_dependencies(project_root: Path) -> None:
    """Check and synchronize project dependencies using uv.

    Runs 'uv sync --dev' to ensure all project dependencies (including
    development dependencies) are properly installed and synchronized.

    Args:
        project_root: Path to the project root directory

    Raises:
        typer.Exit: If dependency sync fails, times out, or encounters errors
    """
    try:
        result = subprocess.run(
            ["uv", "sync", "--dev"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=300,  # 5 minute timeout for large dependency trees
            check=False,
        )
        if result.returncode != 0:
            console.print("[red]❌ Dependency synchronization failed[/red]")
            console.print(f"   [dim]{result.stderr}[/dim]")
            console.print(
                "   💡 [dim]Hint: Check your pyproject.toml and network connectivity[/dim]"
            )
            logger.error(
                "Dependency sync failed",
                stderr=result.stderr,
                returncode=result.returncode,
            )
            raise typer.Exit(1)

        logger.debug("Dependencies synced successfully", project_root=str(project_root))

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Dependency sync timed out (5 minutes)[/red]")
        console.print(
            "   💡 [dim]Hint: Large dependency trees may take longer. Check network speed.[/dim]"
        )
        logger.error("Dependency sync timed out")
        raise typer.Exit(1) from None
    except typer.Exit:
        raise  # Re-raise typer.Exit without wrapping
    except subprocess.SubprocessError as e:
        console.print(f"[red]❌ Failed to sync dependencies: {e}[/red]")
        console.print(
            "   💡 [dim]Hint: Ensure uv is properly installed and accessible[/dim]"
        )
        logger.error("Dependency sync subprocess error", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


def _install_precommit_hooks(project_root: Path) -> bool:
    """Install pre-commit hooks with graceful failure handling.

    Attempts to install pre-commit hooks using 'pre-commit install'.
    This operation is non-critical and will not fail the overall setup
    if pre-commit is not available.

    Args:
        project_root: Path to the project root directory

    Returns:
        True if hooks were installed successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["pre-commit", "install"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=60,  # 1 minute timeout
            check=False,
        )
        if result.returncode == 0:
            logger.debug(
                "Pre-commit hooks installed successfully",
                project_root=str(project_root),
            )
            return True
        else:
            console.print("[yellow]⚠️  Pre-commit hooks installation failed[/yellow]")
            console.print(f"   [dim]{result.stderr}[/dim]")
            logger.warning(
                "Pre-commit hooks installation failed",
                stderr=result.stderr,
                returncode=result.returncode,
            )
            return False

    except FileNotFoundError:
        console.print("[yellow]⚠️  pre-commit command not found (optional)[/yellow]")
        console.print("   💡 [dim]Install with: pip install pre-commit[/dim]")
        logger.warning("Pre-commit not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        console.print(
            "[yellow]⚠️  Pre-commit installation timed out (1 minute)[/yellow]"
        )
        logger.warning("Pre-commit installation timed out")
        return False
    except subprocess.SubprocessError as e:
        console.print(f"[yellow]⚠️  Pre-commit subprocess error: {e}[/yellow]")
        logger.warning("Pre-commit subprocess error", error=str(e))
        return False


def _check_core_dependencies() -> None:
    """Check if core Python dependencies can be imported.

    Validates that all essential Python packages required by the CLI
    are installed and importable. This includes typer, structlog, and rich.

    Raises:
        typer.Exit: If any core dependencies are missing or cannot be imported
    """
    try:
        required_modules = ["typer", "structlog", "rich"]
        missing_modules = []

        for module in required_modules:
            if not importlib.util.find_spec(module):
                missing_modules.append(module)

        if missing_modules:
            console.print(
                f"[red]❌ Missing core dependencies: {', '.join(missing_modules)}[/red]"
            )
            console.print("   💡 [bold]Install dependencies:[/bold] uv sync --dev")
            console.print("   💡 [dim]Or: pip install typer structlog rich[/dim]")
            logger.error(
                "Core dependencies check failed", missing_modules=missing_modules
            )
            raise typer.Exit(1)

        logger.debug("Core dependencies check passed", modules=required_modules)

    except typer.Exit:
        raise  # Re-raise typer.Exit without wrapping
    except ImportError as e:
        console.print(f"[red]❌ Dependency import error: {e}[/red]")
        logger.error("Core dependencies check failed", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


def _check_mcp_adapters(project_root: Path) -> dict[str, dict[str, str]]:
    """Check MCP (Model Context Protocol) adapter readiness for all agents.

    Validates that each agent package has a properly implemented MCP adapter
    by checking for:
    - Presence of mcp_stub.py file with MCPStub class
    - Protocol compliance (_process_request async method)
    - Schema validation (AgentInput/AgentOutput contract usage)

    Args:
        project_root: Path to the project root directory

    Returns:
        Dictionary mapping agent names to their validation results.
        Each result contains "detected_stub", "protocol_compliance",
        and "schema_validation" with ✅ or ❌ status indicators.
    """
    results: dict[str, dict[str, str]] = {}
    packages_dir = project_root / "packages"

    for agent_name in AGENT_PACKAGES:
        agent_path = packages_dir / agent_name
        mcp_adapter_path = agent_path / "adapters" / "mcp_stub.py"

        # Initialize result with all checks failed
        result: dict[str, str] = {
            "detected_stub": "❌",
            "protocol_compliance": "❌",
            "schema_validation": "❌",
        }

        try:
            if agent_path.exists() and mcp_adapter_path.exists():
                content = mcp_adapter_path.read_text(encoding="utf-8")

                # Check 1: Stub class detection
                if "class" in content and "MCPStub" in content:
                    result["detected_stub"] = "✅"

                    # Check 2: Protocol compliance (async request processing)
                    if "_process_request" in content and "async def" in content:
                        result["protocol_compliance"] = "✅"

                    # Check 3: Schema validation (contract types present)
                    if "AgentInput" in content and "AgentOutput" in content:
                        result["schema_validation"] = "✅"

                logger.debug(
                    "MCP adapter check completed", agent=agent_name, result=result
                )
            else:
                logger.warning(
                    "MCP adapter not found",
                    agent=agent_name,
                    path=str(mcp_adapter_path),
                    agent_exists=agent_path.exists(),
                    adapter_exists=mcp_adapter_path.exists(),
                )

        except OSError as e:
            logger.error(
                "File system error checking MCP adapter", agent=agent_name, error=str(e)
            )
        except Exception as e:
            logger.error(
                "Unexpected error checking MCP adapter",
                agent=agent_name,
                error=str(e),
                exc_info=True,
            )

        results[agent_name] = result

    return results


def _get_test_payload(agent_type: str) -> dict[str, Any]:
    """Get appropriate test payload for specific agent type.

    Returns a realistic test payload tailored to each agent's expected
    input schema. This ensures proper validation during simulation runs.

    Args:
        agent_type: The agent package name (e.g., "agent-ingest")

    Returns:
        Dictionary containing agent-specific test data
    """
    payloads: dict[str, dict[str, Any]] = {
        "agent-ingest": {"data": "test_data", "source": "cli_simulation"},
        "agent-retrieval": {"query": {"term": "test"}, "limit": 10},
        "agent-scoring": {"data": "test_item", "model": "default"},
        "agent-notify": {
            "recipient": "admin@test.com",
            "channel": "email",
            "message": "CLI test notification",
        },
        "agent-billing": {
            "amount": 100.0,
            "currency": "USD",
            "customer_id": "cust_test_123",
        },
    }
    # Return agent-specific payload or generic fallback
    return payloads.get(agent_type, {"test": "data", "source": "generic"})


def _is_mcp_enabled() -> bool:
    """Check if MCP mode is enabled via environment variable.

    Reads the AGS_MCP_ENABLED environment variable to determine if
    the CLI should use MCP adapters for agent communication.

    Returns:
        True if MCP is enabled, False otherwise
    """
    return os.getenv("AGS_MCP_ENABLED", "false").lower() in ("true", "1", "yes")


@app.callback()
def main(
    version: bool | None = typer.Option(  # noqa: ARG001 - used by callback
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Enable verbose logging"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress non-essential output"
    ),
) -> None:
    """AgSense CLI - Intelligent Agent Orchestration Platform.

    A comprehensive command-line interface for managing the AgSense platform,
    including development setup, testing, MCP validation, and agent orchestration.

    Args:
        version: Show version information and exit (handled by eager callback)
        verbose: Enable detailed debug logging output
        quiet: Suppress non-essential console output (errors still shown)
    """
    # Set global quiet mode for use by commands
    global _quiet_mode  # noqa: PLW0603 - required for CLI-wide state
    _quiet_mode = quiet

    try:
        # Configure logging based on verbosity level
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
                    structlog.dev.ConsoleRenderer(),  # Pretty console output for verbose mode
                ],
                wrapper_class=structlog.stdlib.BoundLogger,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
                log_level=logging.DEBUG,
            )
        elif quiet:
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
                    structlog.processors.JSONRenderer(),
                ],
                wrapper_class=structlog.stdlib.BoundLogger,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
                log_level=logging.WARNING,
            )

        logger.info("AgSense CLI initialized", verbose=verbose, quiet=quiet)

    except Exception as e:
        # Fallback logging configuration if structlog fails
        # This should rarely happen as structlog is a core dependency
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Failed to configure logging: {e}")
        if not quiet:
            console.print(f"[yellow]⚠️  Logging configuration warning: {e}[/yellow]")
            console.print("   💡 [dim]CLI will continue with basic logging[/dim]")


@app.command()
def dev_setup() -> None:
    """Set up development environment and verify installation.

    Performs comprehensive development environment setup including:
    - Python version validation
    - uv package manager verification
    - Project structure validation
    - Dependency synchronization
    - Pre-commit hooks installation
    """
    console.print(
        Panel.fit(
            "[bold blue]AgSense Development Setup[/bold blue]\n"
            "Setting up development environment...",
            border_style="blue",
        )
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Check Python version
            task1 = progress.add_task("Checking Python version...", total=None)
            _check_python_version()
            progress.update(task1, description="✅ Python version OK")

            # Check uv installation
            task2 = progress.add_task("Checking uv installation...", total=None)
            _check_uv_installation()
            progress.update(task2, description="✅ uv installed")

            # Check project structure
            task3 = progress.add_task("Checking project structure...", total=None)
            project_root = Path.cwd()
            _check_project_structure(project_root)
            progress.update(task3, description="✅ Project structure OK")

            # Check dependencies
            task4 = progress.add_task("Checking dependencies...", total=None)
            _check_dependencies(project_root)
            progress.update(task4, description="✅ Dependencies synced")

            # Install pre-commit hooks
            task5 = progress.add_task("Installing pre-commit hooks...", total=None)
            if _install_precommit_hooks(project_root):
                progress.update(task5, description="✅ Pre-commit hooks installed")
            else:
                progress.update(task5, description="⚠️  Pre-commit skipped")

        console.print("\n[green]🎉 Development environment setup complete![/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print(
            "  • Run [bold cyan]ags test[/bold cyan] to verify everything works"
        )
        console.print(
            "  • Run [bold cyan]ags mcp-check[/bold cyan] to check agent readiness"
        )
        console.print("  • Run [bold cyan]make run[/bold cyan] to start all agents")

    except typer.Exit:
        # Re-raise typer.Exit to maintain proper exit codes
        raise
    except Exception as e:
        logger.error("Development setup failed", error=str(e), exc_info=True)
        console.print(f"\n[red]❌ Development setup failed: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def test() -> None:
    """Run tests and verify the installation.

    Executes the complete test suite using pytest to verify that the
    AgSense platform is properly installed and configured.
    """
    console.print(
        Panel.fit(
            "[bold blue]AgSense Test Suite[/bold blue]\n"
            "Running tests to verify installation...",
            border_style="blue",
        )
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Run pytest
            task1 = progress.add_task("Running tests...", total=None)
            try:
                result = subprocess.run(
                    ["uv", "run", "pytest", "tests/", "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd(),
                    timeout=600,  # 10 minute timeout for tests
                )

                if result.returncode == 0:
                    progress.update(task1, description="✅ All tests passed")
                    console.print(f"\n[green]{result.stdout}[/green]")
                    logger.info("All tests passed successfully")
                else:
                    progress.update(task1, description="❌ Some tests failed")
                    console.print("\n[red]Test failures:[/red]")
                    console.print(result.stdout)
                    console.print(result.stderr)
                    logger.error(
                        "Test suite failed", stdout=result.stdout, stderr=result.stderr
                    )
                    raise typer.Exit(1)

            except subprocess.TimeoutExpired:
                progress.update(task1, description="❌ Tests timed out")
                console.print("[red]❌ Test execution timed out (10 minutes)[/red]")
                logger.error("Test execution timed out")
                raise typer.Exit(1) from None
            except subprocess.SubprocessError as e:
                progress.update(task1, description="❌ Failed to run tests")
                console.print(f"[red]❌ Failed to run tests: {e}[/red]")
                logger.error("Failed to run tests", error=str(e))
                raise typer.Exit(1) from e

        console.print("\n[green]🎉 All tests passed![/green]")

    except typer.Exit:
        # Re-raise typer.Exit to maintain proper exit codes
        raise
    except Exception as e:
        logger.error("Test execution failed", error=str(e), exc_info=True)
        console.print(f"\n[red]❌ Test execution failed: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def mcp_check() -> None:
    """Check MCP (Model Context Protocol) readiness across all agents.

    Validates MCP adapter compliance, schema validation, and environment
    configuration for all agent packages in the AgSense platform.
    """
    console.print(
        Panel.fit(
            "[bold blue]AgSense MCP Readiness Check[/bold blue]\n"
            "Validating MCP adapter compliance, schema, and env flags...",
            border_style="blue",
        )
    )

    try:
        # Check MCP feature flag
        mcp_enabled = _is_mcp_enabled()
        console.print(
            f"\n[bold]Environment Flag:[/bold] AGS_MCP_ENABLED={'✅ Enabled' if mcp_enabled else '❌ Disabled'}"
        )

        # Create readiness table
        table = Table(title="Agent MCP Readiness Status", show_lines=True)
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Detected Stub", justify="center")
        table.add_column("Protocol Compliance", justify="center")
        table.add_column("Schema Validation", justify="center")
        table.add_column("Env Flag", justify="center")

        project_root = Path.cwd()
        mcp_results = _check_mcp_adapters(project_root)

        all_ready = True
        for agent_name in AGENT_PACKAGES:
            result = mcp_results.get(agent_name, {})

            # Check if all validations passed
            if any(status == "❌" for status in result.values()):
                all_ready = False

            env_flag_status = "✅" if mcp_enabled else "⚠️"
            table.add_row(
                agent_name,
                result.get("detected_stub", "❌"),
                result.get("protocol_compliance", "❌"),
                result.get("schema_validation", "❌"),
                env_flag_status,
            )

        console.print(table)

        # Summary
        total_agents = len(AGENT_PACKAGES)
        successful_agents = sum(
            1
            for result in mcp_results.values()
            if all(status == "✅" for status in result.values())
        )

        if all_ready and mcp_enabled:
            console.print(
                f"\n[green]🎉 All {total_agents} agents are fully MCP-ready![/green]"
            )
            console.print("\n[bold]Next steps:[/bold]")
            console.print(
                "  • Run [bold cyan]ags agent run all --trace[/bold cyan] to test orchestration"
            )
            console.print("  • Check logs for proper request ID, latency metrics")
            logger.info(
                "All agents are MCP-ready", total_agents=total_agents, mcp_enabled=True
            )
        elif all_ready and not mcp_enabled:
            console.print(
                "\n[yellow]⚠️  All adapters are ready, but MCP is disabled[/yellow]"
            )
            console.print("\nTo enable MCP mode, run:")
            console.print("  [bold cyan]export AGS_MCP_ENABLED=true[/bold cyan]")
            logger.warning(
                "MCP adapters ready but MCP disabled",
                successful_agents=successful_agents,
            )
        else:
            console.print(
                f"\n[red]❌ Only {successful_agents}/{total_agents} agents are MCP-ready[/red]"
            )
            console.print("Run [bold cyan]make setup[/bold cyan] to complete the setup")
            logger.warning(
                "Some agents not MCP-ready",
                successful_agents=successful_agents,
                total_agents=total_agents,
            )

    except Exception as e:
        logger.error("MCP check failed", error=str(e), exc_info=True)
        console.print(f"\n[red]❌ MCP check failed: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def health_check() -> None:
    """Check system health and agent status.

    Performs comprehensive health checks including:
    - Python environment validation
    - Core dependency verification
    - Project structure validation
    - System resource availability
    """
    console.print(
        Panel.fit(
            "[bold blue]AgSense Health Check[/bold blue]\n"
            "Checking system and agent health...",
            border_style="blue",
        )
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Check Python environment
            task1 = progress.add_task("Checking Python environment...", total=None)
            _check_python_version()
            progress.update(task1, description="✅ Python environment OK")

            # Check dependencies
            task2 = progress.add_task("Checking dependencies...", total=None)
            _check_core_dependencies()
            progress.update(task2, description="✅ Core dependencies OK")

            # Check project structure
            task3 = progress.add_task("Checking project structure...", total=None)
            project_root = Path.cwd()
            missing_files = [
                f for f in REQUIRED_FILES if not (project_root / f).exists()
            ]
            if missing_files:
                progress.update(
                    task3, description=f"❌ Missing files: {', '.join(missing_files)}"
                )
                console.print(
                    f"[red]❌ Missing files: {', '.join(missing_files)}[/red]"
                )
                logger.error(
                    "Project structure check failed", missing_files=missing_files
                )
                raise typer.Exit(1)
            else:
                progress.update(task3, description="✅ Project structure OK")
                logger.debug("Project structure check passed", files=REQUIRED_FILES)

        console.print("\n[green]🎉 System health check passed![/green]")
        logger.info("System health check completed successfully")

    except typer.Exit:
        # Re-raise typer.Exit to maintain proper exit codes
        raise
    except Exception as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        console.print(f"\n[red]❌ Health check failed: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def info() -> None:
    """Show system information and configuration.

    Displays comprehensive system information including:
    - Python version and platform details
    - Working directory and CLI version
    - Environment variables and configuration
    """
    console.print(
        Panel.fit(
            "[bold blue]AgSense System Information[/bold blue]", border_style="blue"
        )
    )

    try:
        # System info table
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Property", style="cyan", no_wrap=True)
        info_table.add_column("Value", style="white")

        # Get system information safely
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        platform_name = f"{platform.system()} {platform.release()}"
        architecture = platform.machine()
        working_dir = str(Path.cwd())

        info_table.add_row("Python Version", python_version)
        info_table.add_row("Platform", platform_name)
        info_table.add_row("Architecture", architecture)
        info_table.add_row("Working Directory", working_dir)
        info_table.add_row("CLI Version", CLI_VERSION)

        console.print(info_table)

        # Environment variables
        env_vars = [
            "PATH",
            "PYTHONPATH",
            "VIRTUAL_ENV",
            "CONDA_DEFAULT_ENV",
            "AGS_MCP_ENABLED",
        ]
        env_table = Table(title="Environment Variables")
        env_table.add_column("Variable", style="cyan")
        env_table.add_column("Value", style="dim")

        for var in env_vars:
            value = os.getenv(var, "Not set")
            if len(value) > 50:
                value = value[:47] + "..."
            env_table.add_row(var, value)

        console.print(env_table)

        # Log system info for debugging
        logger.debug(
            "System information displayed",
            python_version=python_version,
            platform=platform_name,
            architecture=architecture,
        )

    except Exception as e:
        logger.error("Failed to display system information", error=str(e))
        console.print(f"[red]❌ Failed to display system information: {e}[/red]")
        raise typer.Exit(1) from e


# Create a subcommand group for agent operations
agent_app = typer.Typer(name="agent", help="Agent management commands")
app.add_typer(agent_app, name="agent")


@agent_app.command("run")
def agent_run(
    target: str = typer.Argument(..., help="Target agent or 'all' for all agents"),
    trace: bool = typer.Option(False, "--trace", help="Enable request flow tracing"),
) -> None:
    """Run agent orchestrator simulation with optional tracing.

    Executes agent simulation with comprehensive error handling and logging.
    Supports both MCP-enabled and local adapter modes.

    Args:
        target: Agent name to run or 'all' for all agents
        trace: Enable detailed request flow tracing
    """
    console.print(
        Panel.fit(
            "[bold blue]AgSense Agent Orchestrator Simulation[/bold blue]\n"
            f"Running: {target}",
            border_style="blue",
        )
    )

    try:
        # Validate target
        if target != "all" and target not in AGENT_PACKAGES:
            console.print(f"[red]❌ Invalid agent target: {target}[/red]")
            console.print(f"Available agents: {', '.join(AGENT_PACKAGES)}, or 'all'")
            logger.error(
                "Invalid agent target", target=target, available=AGENT_PACKAGES
            )
            raise typer.Exit(1)

        # Check MCP mode
        mcp_enabled = _is_mcp_enabled()
        console.print(
            f"\n[bold]MCP Mode:[/bold] {'✅ Enabled' if mcp_enabled else '❌ Disabled (using local adapters)'}"
        )

        if not mcp_enabled:
            console.print(
                "[yellow]💡 Tip: Enable MCP mode with 'export AGS_MCP_ENABLED=true'[/yellow]\n"
            )

        # Run the simulation
        try:
            asyncio.run(_run_agent_simulation(target, trace))
        except asyncio.TimeoutError:
            console.print("[red]❌ Simulation timed out[/red]")
            logger.error("Agent simulation timed out")
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]❌ Simulation failed: {e}[/red]")
            logger.error("Agent simulation error", error=str(e), exc_info=True)
            raise typer.Exit(1) from e

    except typer.Exit:
        # Re-raise typer.Exit to maintain proper exit codes
        raise
    except Exception as e:
        logger.error("Agent run command failed", error=str(e), exc_info=True)
        console.print(f"[red]❌ Agent run failed: {e}[/red]")
        raise typer.Exit(1) from e


async def _run_agent_simulation(target: str, trace: bool) -> None:
    """Run the actual agent simulation with comprehensive error handling.

    Executes agent simulation by sending test requests to each agent through
    their MCP adapters (if enabled) or via local simulation. Tracks request
    IDs, latency, and execution status for each agent.

    Args:
        target: Agent name to test or 'all' for all agents
        trace: Enable detailed request flow tracing with Rich tree output

    Raises:
        Various exceptions caught and logged for per-agent failures.
        Does not raise on individual agent failures to allow batch testing.
    """
    # Determine which agents to test based on target
    agents_to_test = AGENT_PACKAGES.copy() if target == "all" else [target]

    console.print(f"\n[bold]Testing {len(agents_to_test)} agent(s)...[/bold]\n")

    # Add packages directory to Python path for dynamic imports
    project_root = Path.cwd()
    sys.path.insert(0, str(project_root / "packages"))

    mcp_enabled = _is_mcp_enabled()
    results = []
    trace_tree = Tree("🔄 [bold cyan]Request Flow Trace[/bold cyan]") if trace else None

    # Main simulation loop - test each agent independently
    for agent_type in agents_to_test:
        # Generate unique identifiers for request tracking
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        correlation_id = f"corr_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        try:
            # Get agent-specific test payload
            payload = _get_test_payload(agent_type)

            # Branch 1: MCP-enabled mode - use real adapters
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

                    # Import contract types for type-safe request construction
                    from core.models.contracts import AgentInput, Priority

                    # Create typed agent request
                    agent_input = AgentInput(
                        request_id=request_id,
                        agent_type=agent_type,
                        payload=payload,
                        priority=Priority.NORMAL,
                        correlation_id=correlation_id,
                    )

                    # Send request through MCP adapter and await response
                    result = await adapter.send_request(agent_input)

                    latency_ms = (time.time() - start_time) * 1000

                    # Log structured telemetry for observability
                    logger.info(
                        "Agent request completed",
                        ts=time.time(),
                        agent=agent_type,
                        request_id=request_id,
                        latency_ms=round(latency_ms, 2),
                        status="ok" if result.status == "completed" else "error",
                        message=f"Processed by {agent_type}",
                    )

                    results.append(
                        {
                            "agent": agent_type,
                            "request_id": request_id,
                            "status": result.status,
                            "latency_ms": round(latency_ms, 2),
                        }
                    )

                    # Add to trace tree
                    if trace and trace_tree:
                        agent_node = trace_tree.add(f"[cyan]{agent_type}[/cyan]")
                        agent_node.add(f"[dim]Request ID:[/dim] {request_id}")
                        agent_node.add(
                            f"[dim]Status:[/dim] [green]{result.status}[/green]"
                        )
                        agent_node.add(f"[dim]Latency:[/dim] {round(latency_ms, 2)}ms")
                        agent_node.add(f"[dim]Correlation ID:[/dim] {correlation_id}")

                except ImportError as e:
                    console.print(
                        f"[yellow]⚠️  {agent_type}: Adapter not found (skipping)[/yellow]"
                    )
                    logger.warning(f"Could not import {agent_type}", error=str(e))
                    results.append(
                        {
                            "agent": agent_type,
                            "request_id": request_id,
                            "status": "skipped",
                            "latency_ms": 0,
                        }
                    )
            else:
                # Branch 2: Local simulation mode (no MCP adapters)
                await asyncio.sleep(0.1)  # Simulate processing time
                latency_ms = (time.time() - start_time) * 1000

                logger.info(
                    "Agent request simulated locally",
                    ts=time.time(),
                    agent=agent_type,
                    request_id=request_id,
                    latency_ms=round(latency_ms, 2),
                    status="ok",
                    message=f"Processed by {agent_type} (local)",
                )

                results.append(
                    {
                        "agent": agent_type,
                        "request_id": request_id,
                        "status": "completed",
                        "latency_ms": round(latency_ms, 2),
                    }
                )

                if trace and trace_tree:
                    agent_node = trace_tree.add(
                        f"[cyan]{agent_type}[/cyan] (local mode)"
                    )
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
                error=str(e),
                exc_info=True,
            )
            results.append(
                {
                    "agent": agent_type,
                    "request_id": request_id,
                    "status": "error",
                    "latency_ms": round(latency_ms, 2),
                }
            )

            if trace and trace_tree:
                agent_node = trace_tree.add(f"[red]{agent_type}[/red]")
                agent_node.add(f"[dim]Request ID:[/dim] {request_id}")
                agent_node.add("[dim]Status:[/dim] [red]error[/red]")
                agent_node.add(f"[dim]Error:[/dim] {str(e)}")

    # Print trace tree if enabled
    if trace and trace_tree:
        console.print(trace_tree)

    # Print results table
    results_table = Table(title="\n📊 Agent Execution Results", show_lines=True)
    results_table.add_column("Agent", style="cyan")
    results_table.add_column("Request ID", style="dim")
    results_table.add_column("Status", justify="center")
    results_table.add_column("Latency (ms)", justify="right")

    for result in results:
        status_display = (
            "[green]✅ " + result["status"] + "[/green]"
            if result["status"] == "completed"
            else "[red]❌ " + result["status"] + "[/red]"
        )
        results_table.add_row(
            result["agent"],
            result["request_id"],
            status_display,
            str(result["latency_ms"]),
        )

    console.print(results_table)

    # Calculate summary statistics with safe division
    total = len(results)
    successful = sum(1 for r in results if r["status"] == "completed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = total - successful - skipped

    # Calculate average latency only for successful requests (avoid division by zero)
    total_latency = sum(r["latency_ms"] for r in results if r["latency_ms"] > 0)
    avg_latency = total_latency / successful if successful > 0 else 0.0

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  • Total agents tested: {total}")
    console.print(f"  • Successful: [green]{successful}[/green]")
    console.print(f"  • Skipped: [yellow]{skipped}[/yellow]")
    console.print(f"  • Failed: [red]{failed}[/red]")
    console.print(f"  • Average latency: {round(avg_latency, 2)}ms")

    # Log summary for debugging
    logger.info(
        "Agent simulation completed",
        total=total,
        successful=successful,
        skipped=skipped,
        failed=failed,
        avg_latency=round(avg_latency, 2),
        mcp_enabled=mcp_enabled,
    )

    if successful == total:
        console.print("\n[green]🎉 All agents executed successfully![/green]")
    elif failed > 0:
        console.print("\n[red]❌ Some agents failed execution[/red]")
    else:
        console.print("\n[yellow]⚠️  Some agents were skipped[/yellow]")


if __name__ == "__main__":
    app()
