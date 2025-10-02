#!/usr/bin/env python3
"""
Chaos Suite Validation Script - Stage 6.5
Validates the chaos engineering suite fixes before CI/CD deployment.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, timeout=30):
    """Run a shell command with timeout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"

async def test_health_endpoints():
    """Test that health endpoints are working."""
    logger.info("🏥 Testing health endpoints...")
    
    # Start the application in background
    logger.info("Starting application...")
    proc = subprocess.Popen(
        ["python3", "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for startup
    await asyncio.sleep(5)
    
    try:
        # Test health endpoints
        endpoints = ["/api/health", "/api/health/ready", "/api/health/live"]
        
        for endpoint in endpoints:
            cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5001{endpoint}"
            code, stdout, stderr = run_command(cmd, timeout=10)
            
            if code == 0 and stdout.strip() == "200":
                logger.info(f"✅ {endpoint} - OK")
            else:
                logger.error(f"❌ {endpoint} - Failed (HTTP {stdout.strip()})")
                return False
        
        return True
        
    finally:
        # Clean up
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

def test_chaos_configuration():
    """Test chaos scenarios configuration."""
    logger.info("⚙️  Testing chaos configuration...")
    
    config_file = Path("deploy/chaos_scenarios.yml")
    if not config_file.exists():
        logger.error(f"❌ Configuration file not found: {config_file}")
        return False
    
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['slo_targets', 'slo_severity', 'scenarios']
        for section in required_sections:
            if section not in config:
                logger.error(f"❌ Missing required section: {section}")
                return False
            logger.info(f"✅ Found section: {section}")
        
        # Check SLO severity levels
        severity = config.get('slo_severity', {})
        if 'blocking' not in severity or 'warning' not in severity:
            logger.error("❌ Missing blocking/warning severity levels")
            return False
        
        logger.info("✅ SLO severity levels configured")
        
        # Check scenarios
        scenarios = config.get('scenarios', [])
        logger.info(f"✅ Found {len(scenarios)} chaos scenarios")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False

def test_resilience_validator():
    """Test resilience validator with new features."""
    logger.info("🎯 Testing resilience validator...")
    
    try:
        # Import and test validator
        sys.path.insert(0, str(Path.cwd()))
        from deploy.resilience_validator import ResilienceValidator, SLOSeverity
        
        validator = ResilienceValidator(
            target_url="http://localhost:5001",
            config_path="deploy/chaos_scenarios.yml"
        )
        
        # Check if severity levels are loaded
        if validator.slo_severity is None:
            logger.error("❌ SLO severity levels not loaded")
            return False
        
        logger.info("✅ SLO severity levels loaded")
        logger.info(f"   Warning MTTR: {validator.slo_severity.warning.mttr_seconds}s")
        logger.info(f"   Blocking MTTR: {validator.slo_severity.blocking.mttr_seconds}s")
        
        # Test validation with mock data
        validator.metrics.mttr = 50.0  # Between warning (45s) and blocking (60s)
        validator.metrics.error_rate_percent = 10.0  # Between warning (8%) and blocking (15%)
        validator.metrics.availability_percent = 90.0  # Between warning (92%) and blocking (85%)
        
        result = validator.validate_slos()
        
        if not result.passed:
            logger.error("❌ Validation should pass with mock data in warning range")
            return False
        
        if len(result.warnings) == 0:
            logger.error("❌ Should have warnings for metrics in warning range")
            return False
        
        logger.info(f"✅ Validation passed with {len(result.warnings)} warnings")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Resilience validator test failed: {e}")
        return False

def test_chaos_scripts():
    """Test chaos injection scripts."""
    logger.info("🔥 Testing chaos scripts...")
    
    scripts = [
        "deploy/chaos_injector.py",
        "deploy/resilience_validator.py", 
        "deploy/run_chaos_tests.sh"
    ]
    
    for script in scripts:
        if not Path(script).exists():
            logger.error(f"❌ Script not found: {script}")
            return False
        
        # Check if script is executable (for shell scripts)
        if script.endswith('.sh'):
            if not Path(script).stat().st_mode & 0o111:
                logger.warning(f"⚠️  Script not executable: {script}")
        
        logger.info(f"✅ Found script: {script}")
    
    # Test dry-run chaos injection
    logger.info("Testing dry-run chaos injection...")
    cmd = "python3 deploy/chaos_injector.py --dry-run --config deploy/chaos_scenarios.yml --output /tmp/test_chaos_results.json"
    code, stdout, stderr = run_command(cmd, timeout=60)
    
    if code != 0:
        logger.error(f"❌ Dry-run chaos injection failed: {stderr}")
        return False
    
    logger.info("✅ Dry-run chaos injection successful")
    
    return True

async def main():
    """Main validation function."""
    logger.info("🧪 Starting Chaos Suite Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Configuration", test_chaos_configuration),
        ("Resilience Validator", test_resilience_validator),
        ("Chaos Scripts", test_chaos_scripts),
        ("Health Endpoints", test_health_endpoints),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running test: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Validation Summary")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All validation tests passed! Chaos suite is ready for deployment.")
        return 0
    else:
        logger.error("💥 Some validation tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)