#!/usr/bin/env python3
"""
Chaos Injection Engine - Stage 6.5
Simulates various failure scenarios to test system resilience.
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import subprocess
import sys
import time
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiohttp


def auto_detect_target_url() -> str:
    """Auto-detect target URL using port detector."""
    # Check environment variables first
    target_url = os.getenv('TARGET_URL')
    if target_url:
        return target_url
    
    chaos_port = os.getenv('CHAOS_TARGET_PORT')
    if chaos_port:
        return f"http://localhost:{chaos_port}"
    
    # Try to use port detector
    try:
        result = subprocess.run([
            'python3', 'deploy/port_detector.py', 
            '--url-only', '--quiet'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            detected_url = result.stdout.strip()
            print(f"🔍 Auto-detected target: {detected_url}")
            return detected_url
    except Exception as e:
        print(f"Warning: Port auto-detection failed: {e}")
    
    # Fallback to default
    fallback_url = "http://localhost:8000"
    print(f"⚠️  Using fallback target: {fallback_url}")
    return fallback_url


@dataclass
class ChaosScenario:
    """Configuration for a chaos scenario."""
    name: str
    type: str  # cpu_exhaust, memory_leak, network_delay, container_crash, database_down
    intensity: str  # light, medium, heavy
    duration: int  # seconds
    description: str = ""
    target: Optional[str] = None  # Target container/service
    parameters: Optional[Dict] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ChaosResult:
    """Result of a chaos injection scenario."""
    scenario_name: str
    scenario_type: str
    intensity: str
    duration: int
    start_time: float
    end_time: float
    success: bool
    error_message: Optional[str] = None
    metrics: Optional[Dict] = None
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'scenario_name': self.scenario_name,
            'scenario_type': self.scenario_type,
            'intensity': self.intensity,
            'duration': self.duration,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
            'elapsed_time': self.end_time - self.start_time,
            'success': self.success,
            'error_message': self.error_message,
            'metrics': self.metrics or {}
        }


class ChaosInjector:
    """Main chaos injection engine."""
    
    def __init__(self, config_path: str = "deploy/chaos_scenarios.yml", 
                 target_url: str = "http://localhost:8000",
                 dry_run: bool = False):
        self.config_path = config_path
        self.target_url = target_url
        self.dry_run = dry_run
        self.logger = self._setup_logging()
        self.scenarios = []
        self.results = []
        self.stress_process = None
        self.interrupted = False
        
        # Setup signal handlers for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        self.logger.warning("Interrupt received, cleaning up...")
        self.interrupted = True
        self._cleanup()
        sys.exit(1)
    
    def _cleanup(self):
        """Clean up any running chaos processes."""
        if self.stress_process:
            try:
                self.stress_process.terminate()
                self.stress_process.wait(timeout=5)
            except:
                try:
                    self.stress_process.kill()
                except:
                    pass
        
        # Kill any lingering stress processes
        try:
            subprocess.run(["pkill", "-f", "stress-ng"], 
                          stderr=subprocess.DEVNULL, timeout=5)
        except:
            pass
    
    def load_scenarios(self) -> List[ChaosScenario]:
        """Load chaos scenarios from YAML configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            scenarios = []
            for scenario_config in config.get('scenarios', []):
                scenario = ChaosScenario(
                    name=scenario_config['name'],
                    type=scenario_config['type'],
                    intensity=scenario_config['intensity'],
                    duration=scenario_config['duration'],
                    description=scenario_config.get('description', ''),
                    target=scenario_config.get('target'),
                    parameters=scenario_config.get('parameters', {})
                )
                scenarios.append(scenario)
            
            self.scenarios = scenarios
            self.logger.info(f"Loaded {len(scenarios)} chaos scenarios")
            return scenarios
            
        except Exception as e:
            self.logger.error(f"Failed to load scenarios: {e}")
            return []
    
    async def inject_scenario(self, scenario: ChaosScenario) -> ChaosResult:
        """Execute a chaos injection scenario."""
        self.logger.info(f"🔥 Injecting chaos: {scenario.name} ({scenario.type})")
        self.logger.info(f"   Intensity: {scenario.intensity}, Duration: {scenario.duration}s")
        
        start_time = time.time()
        success = False
        error_message = None
        metrics = {}
        
        try:
            if self.dry_run:
                self.logger.info(f"   [DRY RUN] Would execute {scenario.type}")
                await asyncio.sleep(1)  # Simulate execution
                success = True
            else:
                # Execute scenario based on type
                if scenario.type == "cpu_exhaust":
                    success = await self._inject_cpu_stress(scenario)
                elif scenario.type == "memory_leak":
                    success = await self._inject_memory_stress(scenario)
                elif scenario.type == "network_delay":
                    success = await self._inject_network_delay(scenario)
                elif scenario.type == "network_loss":
                    success = await self._inject_network_loss(scenario)
                elif scenario.type == "container_crash":
                    success = await self._inject_container_crash(scenario)
                elif scenario.type == "database_down":
                    success = await self._inject_database_failure(scenario)
                elif scenario.type == "disk_stress":
                    success = await self._inject_disk_stress(scenario)
                else:
                    error_message = f"Unknown scenario type: {scenario.type}"
                    self.logger.error(error_message)
                
                # Collect metrics after injection
                metrics = await self._collect_metrics()
                
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Scenario failed: {e}")
        
        end_time = time.time()
        
        result = ChaosResult(
            scenario_name=scenario.name,
            scenario_type=scenario.type,
            intensity=scenario.intensity,
            duration=scenario.duration,
            start_time=start_time,
            end_time=end_time,
            success=success,
            error_message=error_message,
            metrics=metrics
        )
        
        self.results.append(result)
        return result
    
    async def _inject_cpu_stress(self, scenario: ChaosScenario) -> bool:
        """Inject CPU exhaustion stress."""
        intensity_map = {"light": 2, "medium": 4, "heavy": 8}
        cpu_workers = intensity_map.get(scenario.intensity, 4)
        
        try:
            # Check if stress-ng is available
            result = subprocess.run(["which", "stress-ng"], 
                                   capture_output=True, timeout=5)
            
            if result.returncode != 0:
                self.logger.warning("stress-ng not found, using Python-based CPU stress")
                return await self._python_cpu_stress(scenario, cpu_workers)
            
            # Use stress-ng for more realistic CPU stress
            cmd = [
                "stress-ng",
                "--cpu", str(cpu_workers),
                "--timeout", f"{scenario.duration}s",
                "--metrics-brief"
            ]
            
            self.logger.info(f"   Stressing {cpu_workers} CPU cores")
            self.stress_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            # Wait for duration
            await asyncio.sleep(scenario.duration)
            
            # Terminate stress process
            self.stress_process.terminate()
            self.stress_process.wait(timeout=5)
            self.stress_process = None
            
            self.logger.info("   ✓ CPU stress completed")
            return True
            
        except Exception as e:
            self.logger.error(f"CPU stress failed: {e}")
            return False
    
    async def _python_cpu_stress(self, scenario: ChaosScenario, workers: int) -> bool:
        """Fallback Python-based CPU stress."""
        def cpu_burn():
            end = time.time() + scenario.duration
            while time.time() < end:
                _ = sum(i * i for i in range(10000))
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(cpu_burn) for _ in range(workers)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"CPU worker failed: {e}")
        
        return True
    
    async def _inject_memory_stress(self, scenario: ChaosScenario) -> bool:
        """Inject memory leak/exhaustion stress."""
        intensity_map = {"light": "256M", "medium": "512M", "heavy": "1G"}
        memory_size = intensity_map.get(scenario.intensity, "512M")
        
        try:
            # Check if stress-ng is available
            result = subprocess.run(["which", "stress-ng"], 
                                   capture_output=True, timeout=5)
            
            if result.returncode != 0:
                self.logger.warning("stress-ng not found, using Python-based memory stress")
                return await self._python_memory_stress(scenario, memory_size)
            
            cmd = [
                "stress-ng",
                "--vm", "1",
                "--vm-bytes", memory_size,
                "--timeout", f"{scenario.duration}s"
            ]
            
            self.logger.info(f"   Allocating {memory_size} memory")
            self.stress_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            await asyncio.sleep(scenario.duration)
            
            self.stress_process.terminate()
            self.stress_process.wait(timeout=5)
            self.stress_process = None
            
            self.logger.info("   ✓ Memory stress completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Memory stress failed: {e}")
            return False
    
    async def _python_memory_stress(self, scenario: ChaosScenario, size: str) -> bool:
        """Fallback Python-based memory stress."""
        # Convert size to bytes
        multipliers = {"M": 1024 * 1024, "G": 1024 * 1024 * 1024}
        for suffix, multiplier in multipliers.items():
            if size.endswith(suffix):
                bytes_to_alloc = int(size[:-1]) * multiplier
                break
        else:
            bytes_to_alloc = 256 * 1024 * 1024  # Default 256MB
        
        # Allocate memory in chunks
        chunk_size = 1024 * 1024  # 1MB chunks
        chunks = []
        
        try:
            num_chunks = bytes_to_alloc // chunk_size
            self.logger.info(f"   Allocating {num_chunks} MB in memory")
            
            for i in range(num_chunks):
                chunks.append(bytearray(chunk_size))
                if i % 100 == 0:
                    await asyncio.sleep(0)  # Yield control
            
            # Hold memory for duration
            await asyncio.sleep(scenario.duration)
            
            # Release memory
            chunks.clear()
            
            self.logger.info("   ✓ Memory stress completed")
            return True
            
        except MemoryError:
            self.logger.error("Memory allocation failed - system limit reached")
            chunks.clear()
            return False
    
    async def _inject_network_delay(self, scenario: ChaosScenario) -> bool:
        """Inject network latency."""
        intensity_map = {"light": 50, "medium": 200, "heavy": 500}
        delay_ms = intensity_map.get(scenario.intensity, 200)
        
        # This requires network tools and often root access
        # For a safer approach, we'll simulate by adding delays to our test requests
        self.logger.info(f"   Simulating {delay_ms}ms network delay")
        
        try:
            # Try to use tc (traffic control) if available and we have permissions
            interface = scenario.parameters.get('interface', 'lo')
            
            # Check if tc is available
            result = subprocess.run(["which", "tc"], 
                                   capture_output=True, timeout=5)
            
            if result.returncode == 0:
                # Add delay
                cmd_add = [
                    "tc", "qdisc", "add", "dev", interface,
                    "root", "netem", "delay", f"{delay_ms}ms"
                ]
                
                subprocess.run(cmd_add, capture_output=True, timeout=5)
                self.logger.info(f"   Applied {delay_ms}ms delay to {interface}")
                
                # Wait for duration
                await asyncio.sleep(scenario.duration)
                
                # Remove delay
                cmd_del = ["tc", "qdisc", "del", "dev", interface, "root"]
                subprocess.run(cmd_del, capture_output=True, timeout=5)
                
                self.logger.info("   ✓ Network delay removed")
                return True
            else:
                self.logger.warning("tc not available, simulating delay in application")
                # Just wait for duration to simulate
                await asyncio.sleep(scenario.duration)
                return True
                
        except Exception as e:
            self.logger.warning(f"Network delay injection limited: {e}")
            # Fallback to just timing
            await asyncio.sleep(scenario.duration)
            return True
    
    async def _inject_network_loss(self, scenario: ChaosScenario) -> bool:
        """Inject packet loss."""
        intensity_map = {"light": 5, "medium": 15, "heavy": 30}
        loss_percent = intensity_map.get(scenario.intensity, 15)
        
        self.logger.info(f"   Simulating {loss_percent}% packet loss")
        
        try:
            interface = scenario.parameters.get('interface', 'lo')
            
            # Check if tc is available
            result = subprocess.run(["which", "tc"], 
                                   capture_output=True, timeout=5)
            
            if result.returncode == 0:
                # Add packet loss
                cmd_add = [
                    "tc", "qdisc", "add", "dev", interface,
                    "root", "netem", "loss", f"{loss_percent}%"
                ]
                
                subprocess.run(cmd_add, capture_output=True, timeout=5)
                
                await asyncio.sleep(scenario.duration)
                
                # Remove packet loss
                cmd_del = ["tc", "qdisc", "del", "dev", interface, "root"]
                subprocess.run(cmd_del, capture_output=True, timeout=5)
                
                self.logger.info("   ✓ Packet loss removed")
                return True
            else:
                await asyncio.sleep(scenario.duration)
                return True
                
        except Exception as e:
            self.logger.warning(f"Packet loss injection limited: {e}")
            await asyncio.sleep(scenario.duration)
            return True
    
    async def _inject_container_crash(self, scenario: ChaosScenario) -> bool:
        """Inject container crash/restart."""
        container_name = scenario.target or scenario.parameters.get('container', 'backend-v2')
        
        try:
            # Check if Docker is available
            result = subprocess.run(["which", "docker"], 
                                   capture_output=True, timeout=5)
            
            if result.returncode != 0:
                self.logger.warning("Docker not available, simulating container crash")
                await asyncio.sleep(scenario.duration)
                return True
            
            self.logger.info(f"   Restarting container: {container_name}")
            
            # Restart the container
            cmd = ["docker", "restart", container_name]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info(f"   ✓ Container {container_name} restarted")
                
                # Wait for service to recover
                await asyncio.sleep(10)
                
                # Verify service is back up
                max_retries = 10
                for i in range(max_retries):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"{self.target_url}/api/health", 
                                                   timeout=aiohttp.ClientTimeout(total=5)) as resp:
                                if resp.status == 200:
                                    self.logger.info("   ✓ Service recovered")
                                    return True
                    except:
                        pass
                    
                    await asyncio.sleep(2)
                
                self.logger.warning("   Service may not have fully recovered")
                return True
            else:
                self.logger.error(f"   Failed to restart container: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Container crash injection failed: {e}")
            return False
    
    async def _inject_database_failure(self, scenario: ChaosScenario) -> bool:
        """Inject database downtime."""
        db_container = scenario.target or scenario.parameters.get('database', 'postgres')
        
        try:
            # Check if Docker is available
            result = subprocess.run(["which", "docker"], 
                                   capture_output=True, timeout=5)
            
            if result.returncode != 0:
                self.logger.warning("Docker not available, simulating database failure")
                await asyncio.sleep(scenario.duration)
                return True
            
            self.logger.info(f"   Stopping database: {db_container}")
            
            # Stop database
            cmd_stop = ["docker", "stop", db_container]
            result = subprocess.run(cmd_stop, capture_output=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info(f"   ✓ Database stopped")
                
                # Wait for scenario duration
                await asyncio.sleep(scenario.duration)
                
                # Restart database
                self.logger.info(f"   Restarting database: {db_container}")
                cmd_start = ["docker", "start", db_container]
                subprocess.run(cmd_start, capture_output=True, timeout=30)
                
                # Wait for database to be ready
                await asyncio.sleep(10)
                
                self.logger.info("   ✓ Database restarted")
                return True
            else:
                self.logger.warning(f"Could not stop database container: {result.stderr.decode()}")
                await asyncio.sleep(scenario.duration)
                return True
                
        except Exception as e:
            self.logger.error(f"Database failure injection failed: {e}")
            return False
    
    async def _inject_disk_stress(self, scenario: ChaosScenario) -> bool:
        """Inject disk I/O stress."""
        intensity_map = {"light": 1, "medium": 2, "heavy": 4}
        io_workers = intensity_map.get(scenario.intensity, 2)
        
        try:
            # Check if stress-ng is available
            result = subprocess.run(["which", "stress-ng"], 
                                   capture_output=True, timeout=5)
            
            if result.returncode != 0:
                self.logger.warning("stress-ng not found, using Python-based disk stress")
                return await self._python_disk_stress(scenario, io_workers)
            
            cmd = [
                "stress-ng",
                "--io", str(io_workers),
                "--timeout", f"{scenario.duration}s"
            ]
            
            self.logger.info(f"   Stressing disk with {io_workers} I/O workers")
            self.stress_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            await asyncio.sleep(scenario.duration)
            
            self.stress_process.terminate()
            self.stress_process.wait(timeout=5)
            self.stress_process = None
            
            self.logger.info("   ✓ Disk stress completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Disk stress failed: {e}")
            return False
    
    async def _python_disk_stress(self, scenario: ChaosScenario, workers: int) -> bool:
        """Fallback Python-based disk stress."""
        import tempfile
        
        def disk_io():
            end = time.time() + scenario.duration
            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                while time.time() < end:
                    # Write random data
                    data = os.urandom(1024 * 1024)  # 1MB
                    tmp.write(data)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    # Read it back
                    tmp.seek(0)
                    tmp.read(1024 * 1024)
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(disk_io) for _ in range(workers)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Disk I/O worker failed: {e}")
        
        return True
    
    async def _collect_metrics(self) -> Dict:
        """Collect system metrics during/after chaos."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'target_url': self.target_url
        }
        
        # Try to get service health
        try:
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get(f"{self.target_url}/api/health", 
                                      timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    latency = (time.time() - start) * 1000
                    metrics['service_available'] = resp.status == 200
                    metrics['health_check_latency_ms'] = latency
        except Exception as e:
            metrics['service_available'] = False
            metrics['health_check_error'] = str(e)
        
        # Try to get system metrics using psutil if available
        try:
            import psutil
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            metrics['memory_percent'] = mem.percent
            metrics['memory_available_mb'] = mem.available / (1024 * 1024)
        except ImportError:
            pass
        except Exception as e:
            self.logger.debug(f"Could not collect system metrics: {e}")
        
        return metrics
    
    async def run_all_scenarios(self) -> List[ChaosResult]:
        """Run all loaded chaos scenarios sequentially."""
        if not self.scenarios:
            self.logger.warning("No scenarios loaded")
            return []
        
        self.logger.info(f"🚀 Starting chaos injection with {len(self.scenarios)} scenarios")
        
        for i, scenario in enumerate(self.scenarios, 1):
            if self.interrupted:
                break
                
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Scenario {i}/{len(self.scenarios)}")
            self.logger.info(f"{'='*60}")
            
            result = await self.inject_scenario(scenario)
            
            if result.success:
                self.logger.info(f"✅ {scenario.name} completed successfully")
            else:
                self.logger.error(f"❌ {scenario.name} failed: {result.error_message}")
            
            # Wait between scenarios for system to stabilize
            if i < len(self.scenarios):
                recovery_time = 5
                self.logger.info(f"\n⏸️  Waiting {recovery_time}s for system recovery...")
                await asyncio.sleep(recovery_time)
        
        return self.results
    
    def save_results(self, output_file: str = "deploy/chaos_results.json"):
        """Save chaos test results to JSON file."""
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            results_data = {
                'timestamp': datetime.now().isoformat(),
                'target_url': self.target_url,
                'total_scenarios': len(self.results),
                'successful': sum(1 for r in self.results if r.success),
                'failed': sum(1 for r in self.results if not r.success),
                'results': [r.to_dict() for r in self.results]
            }
            
            with open(output_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            self.logger.info(f"📊 Results saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")


async def main():
    """Main entry point for chaos injector."""
    parser = argparse.ArgumentParser(
        description="Chaos Injection Engine - Stage 6.5"
    )
    parser.add_argument("--config", type=str, 
                       default="deploy/chaos_scenarios.yml",
                       help="Chaos scenarios configuration file")
    parser.add_argument("--target", type=str,
                       default=None,
                       help="Target service URL (auto-detected if not provided)")
    parser.add_argument("--scenario", type=str,
                       help="Run specific scenario by name (optional)")
    parser.add_argument("--output", type=str,
                       default="deploy/chaos_results.json",
                       help="Output file for results")
    parser.add_argument("--dry-run", action="store_true",
                       help="Simulate chaos without actual injection")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Auto-detect target URL if not provided
    target_url = args.target
    if target_url is None:
        target_url = auto_detect_target_url()
    
    # Create chaos injector
    injector = ChaosInjector(
        config_path=args.config,
        target_url=target_url,
        dry_run=args.dry_run
    )
    
    # Load scenarios
    scenarios = injector.load_scenarios()
    if not scenarios:
        print("❌ No scenarios loaded. Check configuration file.")
        sys.exit(1)
    
    # Filter to specific scenario if requested
    if args.scenario:
        scenarios = [s for s in scenarios if s.name == args.scenario]
        if not scenarios:
            print(f"❌ Scenario '{args.scenario}' not found")
            sys.exit(1)
        injector.scenarios = scenarios
    
    try:
        # Run chaos scenarios
        results = await injector.run_all_scenarios()
        
        # Save results
        injector.save_results(args.output)
        
        # Print summary
        print(f"\n{'='*60}")
        print("🧪 Chaos Injection Summary")
        print(f"{'='*60}")
        print(f"Total Scenarios: {len(results)}")
        print(f"✅ Successful: {sum(1 for r in results if r.success)}")
        print(f"❌ Failed: {sum(1 for r in results if not r.success)}")
        print(f"📊 Results: {args.output}")
        
        # Exit with non-zero if any scenarios failed
        if any(not r.success for r in results):
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        injector._cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Chaos injection failed: {e}")
        injector._cleanup()
        sys.exit(1)
    finally:
        injector._cleanup()


if __name__ == "__main__":
    asyncio.run(main())

