#!/usr/bin/env python3
"""Main entrypoint for the AgSense Agent Orchestrator."""

import asyncio
import signal
import sys
from pathlib import Path

import structlog

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_orchestrator.orchestrator import AgentOrchestrator

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


class OrchestratorService:
    """Main service class for the Agent Orchestrator."""
    
    def __init__(self) -> None:
        """Initialize the orchestrator service."""
        self.orchestrator = AgentOrchestrator()
        self.shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the orchestrator service."""
        logger.info("Starting AgSense Agent Orchestrator service")
        
        # Set up signal handlers for graceful shutdown
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._signal_handler)
        
        try:
            await self.orchestrator.start()
            
            # Keep the service running until shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Orchestrator service error: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the orchestrator service."""
        logger.info("Stopping AgSense Agent Orchestrator service")
        await self.orchestrator.stop()
        logger.info("Orchestrator service stopped")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown")
        self.shutdown_event.set()


async def main() -> None:
    """Main entrypoint."""
    service = OrchestratorService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
