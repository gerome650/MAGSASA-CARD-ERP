#!/usr/bin/env python3
"""
Chaos Auto-Healer - Stage 7.2
Automatically detects and fixes chaos validation failures.
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ChaosAutoHealer:
    """Automatically heals chaos validation failures."""
    
    # Categorize failure types
    FAILURE_CATEGORIES = {
        'dependency': ['ModuleNotFoundError', 'ImportError', 'No module named'],
        'configuration': ['FileNotFoundError', 'config', 'yaml.scanner.ScannerError'],
        'health_check': ['Connection refused', 'HTTP 000', 'HTTP 404', 'HTTP 500', 'timeout'],
        'injection': ['chaos injection failed', 'scenario failed'],
    }
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5, verbose: bool = False):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.healing_attempts = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - [%(levelname)s] - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def categorize_failure(self, error_message: str) -> str:
        """Categorize the type of failure."""
        error_lower = error_message.lower()
        
        for category, keywords in self.FAILURE_CATEGORIES.items():
            if any(keyword.lower() in error_lower for keyword in keywords):
                return category
        
        return 'unknown'
    
    def analyze_logs(self, log_content: str) -> List[Dict]:
        """Analyze logs to identify failures."""
        failures = []
        
        lines = log_content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for error indicators
            if any(indicator in line.lower() for indicator in ['error', 'failed', 'exception', 'traceback']):
                category = self.categorize_failure(line)
                
                # Get context (5 lines before and after)
                context_start = max(0, i - 5)
                context_end = min(len(lines), i + 6)
                context = '\n'.join(lines[context_start:context_end])
                
                failures.append({
                    'line_number': i + 1,
                    'category': category,
                    'message': line.strip(),
                    'context': context
                })
        
        return failures
    
    def heal_dependency_failure(self, failure: Dict) -> bool:
        """Heal dependency-related failures."""
        self.logger.info("🔧 Healing dependency failure...")
        
        # Extract module name from error
        message = failure['message']
        
        # Try to extract module name
        module_name = None
        if "No module named" in message:
            # Extract: "No module named 'aiohttp'"
            parts = message.split("'")
            if len(parts) >= 2:
                module_name = parts[1]
        elif "ModuleNotFoundError" in message:
            # Look in context for the actual module
            if 'aiohttp' in failure['context']:
                module_name = 'aiohttp'
        
        if not module_name:
            self.logger.warning("Could not extract module name from error")
            return False
        
        self.logger.info(f"Detected missing module: {module_name}")
        
        # Run dependency sentinel to fix
        try:
            result = subprocess.run(
                [sys.executable, 'scripts/chaos_dependency_sentinel.py', '--fix', '--install'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ Dependencies fixed")
                self.healing_attempts.append({
                    'type': 'dependency',
                    'success': True,
                    'module': module_name,
                    'timestamp': datetime.now().isoformat()
                })
                return True
            else:
                self.logger.error(f"❌ Failed to fix dependencies: {result.stderr}")
                self.healing_attempts.append({
                    'type': 'dependency',
                    'success': False,
                    'module': module_name,
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                })
                return False
                
        except Exception as e:
            self.logger.error(f"Exception while fixing dependencies: {e}")
            return False
    
    async def heal_health_check_failure(self, target_url: str, max_wait: int = 60) -> bool:
        """Heal health check failures with smart retries."""
        self.logger.info("🏥 Healing health check failure...")
        self.logger.info(f"Waiting for service at {target_url} to be ready...")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < max_wait:
            attempt += 1
            
            try:
                # Try with curl first (more reliable in CI)
                result = subprocess.run(
                    ['curl', '-f', '-s', f'{target_url}/api/health'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.logger.info(f"✅ Service ready (attempt {attempt})")
                    self.healing_attempts.append({
                        'type': 'health_check',
                        'success': True,
                        'attempts': attempt,
                        'timestamp': datetime.now().isoformat()
                    })
                    return True
                else:
                    self.logger.debug(f"Attempt {attempt}: Service not ready yet")
                    
            except Exception as e:
                self.logger.debug(f"Attempt {attempt}: {e}")
            
            # Exponential backoff
            wait_time = min(2 ** attempt, 10)
            await asyncio.sleep(wait_time)
        
        self.logger.error(f"❌ Service failed to become ready after {max_wait}s")
        self.healing_attempts.append({
            'type': 'health_check',
            'success': False,
            'attempts': attempt,
            'timestamp': datetime.now().isoformat()
        })
        return False
    
    def heal_configuration_failure(self, failure: Dict) -> bool:
        """Heal configuration-related failures."""
        self.logger.info("⚙️  Healing configuration failure...")
        
        # Check if it's a missing file
        if 'FileNotFoundError' in failure['message'] or 'No such file' in failure['message']:
            self.logger.warning("Configuration file missing - cannot auto-heal")
            self.logger.info("Please ensure all required configuration files exist")
            return False
        
        # Check if it's a YAML syntax error
        if 'yaml' in failure['message'].lower():
            self.logger.warning("YAML syntax error - cannot auto-heal")
            self.logger.info("Please fix YAML syntax manually")
            return False
        
        return False
    
    def heal_injection_failure(self, failure: Dict) -> bool:
        """Heal chaos injection failures."""
        self.logger.info("🔥 Healing chaos injection failure...")
        
        # Most injection failures are due to service not being ready
        # This will be handled by health check healing
        
        self.logger.info("Injection failures typically resolve after service is ready")
        return True
    
    async def attempt_healing(self, failures: List[Dict], target_url: str = "http://localhost:8000") -> bool:
        """Attempt to heal all identified failures."""
        if not failures:
            self.logger.info("No failures to heal")
            return True
        
        self.logger.info(f"Found {len(failures)} failure(s) to heal")
        
        # Group failures by category
        failures_by_category = {}
        for failure in failures:
            category = failure['category']
            if category not in failures_by_category:
                failures_by_category[category] = []
            failures_by_category[category].append(failure)
        
        # Heal each category
        all_healed = True
        
        # Priority order: dependencies first, then health checks, then others
        priority_order = ['dependency', 'health_check', 'configuration', 'injection', 'unknown']
        
        for category in priority_order:
            if category not in failures_by_category:
                continue
            
            category_failures = failures_by_category[category]
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Healing {len(category_failures)} {category} failure(s)")
            self.logger.info('='*60)
            
            if category == 'dependency':
                # Only need to heal once for all dependency failures
                if not self.heal_dependency_failure(category_failures[0]):
                    all_healed = False
                    
            elif category == 'health_check':
                # Wait for service to be ready
                if not await self.heal_health_check_failure(target_url):
                    all_healed = False
                    
            elif category == 'configuration':
                for failure in category_failures:
                    if not self.heal_configuration_failure(failure):
                        all_healed = False
                        
            elif category == 'injection':
                for failure in category_failures:
                    if not self.heal_injection_failure(failure):
                        all_healed = False
            
            else:
                self.logger.warning(f"Unknown failure category: {category}")
                all_healed = False
        
        return all_healed
    
    async def run_with_healing(self, command: List[str], log_file: str = None) -> Tuple[bool, str]:
        """Run a command with automatic healing on failure."""
        attempt = 0
        
        while attempt < self.max_retries:
            attempt += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Attempt {attempt}/{self.max_retries}")
            self.logger.info('='*60)
            
            try:
                # Run command
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes
                )
                
                # Save logs if requested
                if log_file:
                    with open(log_file, 'w') as f:
                        f.write(f"=== STDOUT ===\n{result.stdout}\n\n")
                        f.write(f"=== STDERR ===\n{result.stderr}\n")
                
                if result.returncode == 0:
                    self.logger.info("✅ Command succeeded")
                    return True, result.stdout
                
                # Command failed, analyze and heal
                self.logger.warning(f"Command failed with return code {result.returncode}")
                
                # Analyze failures
                combined_output = f"{result.stdout}\n{result.stderr}"
                failures = self.analyze_logs(combined_output)
                
                if not failures:
                    self.logger.warning("No specific failures identified in logs")
                    if attempt < self.max_retries:
                        self.logger.info(f"Retrying in {self.retry_delay}s...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        return False, result.stderr
                
                # Attempt healing
                if await self.attempt_healing(failures):
                    self.logger.info("✅ Healing succeeded, retrying command...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("❌ Healing failed")
                    if attempt < self.max_retries:
                        self.logger.info(f"Retrying anyway in {self.retry_delay}s...")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        return False, result.stderr
                        
            except subprocess.TimeoutExpired:
                self.logger.error("Command timed out")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return False, "Command timed out"
                    
            except Exception as e:
                self.logger.error(f"Exception running command: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return False, str(e)
        
        return False, "Max retries exceeded"
    
    def save_healing_report(self, output_file: str = "reports/chaos_healing_report.json"):
        """Save healing attempts report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_attempts': len(self.healing_attempts),
            'successful_attempts': sum(1 for a in self.healing_attempts if a.get('success')),
            'failed_attempts': sum(1 for a in self.healing_attempts if not a.get('success')),
            'attempts': self.healing_attempts
        }
        
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"📊 Healing report saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save healing report: {e}")


async def main():
    """Main entry point for chaos auto-healer."""
    parser = argparse.ArgumentParser(
        description="Chaos Auto-Healer - Automatically heal chaos validation failures"
    )
    parser.add_argument('--command', nargs='+', required=True,
                       help='Command to run with auto-healing')
    parser.add_argument('--target-url', type=str,
                       default='http://localhost:8000',
                       help='Target service URL for health checks')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum number of retry attempts')
    parser.add_argument('--retry-delay', type=int, default=5,
                       help='Delay between retries in seconds')
    parser.add_argument('--log-file', type=str,
                       help='File to save command logs')
    parser.add_argument('--report', type=str,
                       default='reports/chaos_healing_report.json',
                       help='Output file for healing report')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    print("🤖 Chaos Auto-Healer - Stage 7.2")
    print("=" * 60)
    print(f"Command: {' '.join(args.command)}")
    print(f"Max Retries: {args.max_retries}")
    print(f"Target URL: {args.target_url}")
    print("=" * 60)
    
    # Create healer
    healer = ChaosAutoHealer(
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        verbose=args.verbose
    )
    
    # Run with healing
    success, output = await healer.run_with_healing(args.command, args.log_file)
    
    # Save healing report
    healer.save_healing_report(args.report)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 HEALING SUMMARY")
    print("=" * 60)
    print(f"Total Healing Attempts: {len(healer.healing_attempts)}")
    print(f"Successful: {sum(1 for a in healer.healing_attempts if a.get('success'))}")
    print(f"Failed: {sum(1 for a in healer.healing_attempts if not a.get('success'))}")
    print("=" * 60)
    
    if success:
        print("✅ COMMAND SUCCEEDED")
        sys.exit(0)
    else:
        print("❌ COMMAND FAILED")
        print(f"\nError: {output}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

