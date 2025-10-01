#!/usr/bin/env python3
"""
Enhanced Progressive Rollout with Load Testing Integration
Manages progressive deployment with performance validation at each stage.
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import load testing components
sys.path.append(str(Path(__file__).parent))
from deploy.load_test import LoadTestEngine, LoadTestConfig, PerformanceValidator


class ProgressiveRollout:
    """Enhanced progressive rollout with load testing at each stage."""
    
    def __init__(self, deployment_name: str, namespace: str = "production",
                 load_test_enabled: bool = False, auto_rollback: bool = False):
        self.deployment_name = deployment_name
        self.namespace = namespace
        self.load_test_enabled = load_test_enabled
        self.auto_rollback = auto_rollback
        self.logger = self._setup_logging()
        self.rollout_stages = [
            {'name': '5% Traffic', 'percentage': 5, 'duration': 300},
            {'name': '25% Traffic', 'percentage': 25, 'duration': 600},
            {'name': '50% Traffic', 'percentage': 50, 'duration': 900},
            {'name': '100% Traffic', 'percentage': 100, 'duration': 300}
        ]
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def get_service_url(self, percentage: int) -> str:
        """Get service URL for the current rollout stage."""
        # This would typically integrate with your service discovery or load balancer
        # For now, return a placeholder URL
        base_url = f"http://{self.deployment_name}.{self.namespace}.svc.cluster.local"
        return base_url
    
    async def update_traffic_split(self, percentage: int) -> bool:
        """Update traffic split to route specified percentage to new version."""
        self.logger.info(f"🔄 Updating traffic split to {percentage}%")
        
        try:
            # This would integrate with your traffic management system
            # Examples: Istio, Linkerd, AWS ALB, etc.
            
            # Placeholder implementation using kubectl
            traffic_config = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "VirtualService",
                "metadata": {
                    "name": f"{self.deployment_name}-traffic-split",
                    "namespace": self.namespace
                },
                "spec": {
                    "http": [{
                        "match": [{"uri": {"prefix": "/"}}],
                        "route": [
                            {
                                "destination": {
                                    "host": f"{self.deployment_name}-v2",
                                    "subset": "v2"
                                },
                                "weight": percentage
                            },
                            {
                                "destination": {
                                    "host": f"{self.deployment_name}-v1",
                                    "subset": "v1"
                                },
                                "weight": 100 - percentage
                            }
                        ]
                    }]
                }
            }
            
            # Apply traffic configuration
            config_file = f"/tmp/traffic-split-{percentage}.yaml"
            with open(config_file, 'w') as f:
                json.dump(traffic_config, f, indent=2)
            
            result = subprocess.run(
                ["kubectl", "apply", "-f", config_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ Traffic split updated to {percentage}%")
                return True
            else:
                self.logger.error(f"❌ Failed to update traffic split: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Traffic split error: {e}")
            return False
    
    async def run_stage_load_test(self, stage: Dict, service_url: str) -> Tuple[bool, Dict]:
        """Run load test for a specific rollout stage."""
        if not self.load_test_enabled:
            self.logger.info("⏭️  Load testing disabled for this stage")
            return True, {}
        
        stage_name = stage['name']
        percentage = stage['percentage']
        
        self.logger.info(f"🚀 Running load test for stage: {stage_name}")
        
        try:
            # Scale load test based on traffic percentage
            base_concurrency = 100
            scaled_concurrency = max(10, int(base_concurrency * percentage / 100))
            
            config = LoadTestConfig(
                concurrency=scaled_concurrency,
                duration=min(stage['duration'], 300),  # Cap at 5 minutes
                target_url=service_url,
                request_patterns="sustained"
            )
            
            # Run load test
            engine = LoadTestEngine(config)
            metrics = await engine.run_load_test()
            
            # Validate against SLOs
            validator = PerformanceValidator()
            passed, violations = validator.validate_metrics(metrics)
            
            # Log results
            if passed:
                self.logger.info(f"✅ Stage {stage_name} load test passed")
            else:
                self.logger.error(f"❌ Stage {stage_name} load test failed:")
                for violation in violations:
                    self.logger.error(f"   - {violation}")
            
            return passed, {
                'stage': stage_name,
                'percentage': percentage,
                'metrics': metrics,
                'violations': violations,
                'passed': passed
            }
            
        except Exception as e:
            self.logger.error(f"❌ Stage {stage_name} load test error: {e}")
            return False, {'error': str(e), 'stage': stage_name}
    
    async def monitor_stage_health(self, stage: Dict, duration: int) -> bool:
        """Monitor application health during a rollout stage."""
        stage_name = stage['name']
        self.logger.info(f"📊 Monitoring {stage_name} for {duration}s")
        
        start_time = time.time()
        check_interval = 30  # Check every 30 seconds
        
        while time.time() - start_time < duration:
            try:
                # Check deployment health
                health_ok = await self._check_deployment_health()
                
                if not health_ok:
                    self.logger.error(f"❌ Health check failed for {stage_name}")
                    return False
                
                # Check error rates from monitoring system
                error_rate_ok = await self._check_error_rates()
                
                if not error_rate_ok:
                    self.logger.error(f"❌ Error rate spike detected in {stage_name}")
                    return False
                
                self.logger.debug(f"✅ Health check passed for {stage_name}")
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Health monitoring error: {e}")
                return False
        
        self.logger.info(f"✅ {stage_name} monitoring completed successfully")
        return True
    
    async def _check_deployment_health(self) -> bool:
        """Check Kubernetes deployment health."""
        try:
            result = subprocess.run([
                "kubectl", "get", "deployment", self.deployment_name,
                "-n", self.namespace,
                "-o", "jsonpath={.status.readyReplicas}/{.status.replicas}"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                ready_info = result.stdout.strip()
                if '/' in ready_info:
                    ready, total = ready_info.split('/')
                    return int(ready) == int(total) and int(ready) > 0
            
            return False
            
        except Exception:
            return False
    
    async def _check_error_rates(self) -> bool:
        """Check error rates from monitoring system."""
        # This would integrate with your monitoring system (Prometheus, DataDog, etc.)
        # For now, return True as a placeholder
        return True
    
    async def rollback_deployment(self, reason: str) -> bool:
        """Rollback to previous version."""
        self.logger.warning(f"🔄 Initiating deployment rollback: {reason}")
        
        try:
            # Rollback to previous version
            result = subprocess.run([
                "kubectl", "rollout", "undo", f"deployment/{self.deployment_name}",
                f"--namespace={self.namespace}"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("✅ Deployment rollback completed")
                
                # Reset traffic to 100% old version
                await self.update_traffic_split(0)
                
                # Log rollback event
                await self._log_rollback_event(reason, True)
                return True
            else:
                self.logger.error(f"❌ Rollback failed: {result.stderr}")
                await self._log_rollback_event(reason, False, result.stderr)
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Rollback error: {e}")
            await self._log_rollback_event(reason, False, str(e))
            return False
    
    async def _log_rollback_event(self, reason: str, success: bool, error: str = None):
        """Log rollback event to deployment report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAILED"
        
        log_entry = f"""
## 🔄 Progressive Rollout Rollback

**Timestamp:** {timestamp}  
**Status:** {status}  
**Deployment:** {self.deployment_name}  
**Namespace:** {self.namespace}  
**Reason:** {reason}  
**Auto-triggered:** {'Yes' if self.auto_rollback else 'No'}  
"""
        
        if error:
            log_entry += f"**Error:** {error}\n"
        
        # Append to deployment report
        report_path = Path("deploy/deployment_report.md")
        if report_path.exists():
            with open(report_path, 'a') as f:
                f.write(log_entry)
        else:
            with open(report_path, 'w') as f:
                f.write(f"# Deployment Report\n{log_entry}")
    
    async def execute_progressive_rollout(self) -> bool:
        """Execute the complete progressive rollout process."""
        self.logger.info("🎯 Starting progressive rollout")
        self.logger.info(f"Deployment: {self.deployment_name}")
        self.logger.info(f"Namespace: {self.namespace}")
        self.logger.info(f"Load testing: {'Enabled' if self.load_test_enabled else 'Disabled'}")
        
        rollout_results = []
        
        for i, stage in enumerate(self.rollout_stages):
            stage_name = stage['name']
            percentage = stage['percentage']
            duration = stage['duration']
            
            self.logger.info(f"📋 Stage {i+1}/{len(self.rollout_stages)}: {stage_name}")
            
            # Update traffic split
            traffic_updated = await self.update_traffic_split(percentage)
            if not traffic_updated:
                if self.auto_rollback:
                    await self.rollback_deployment(f"Failed to update traffic split for {stage_name}")
                return False
            
            # Wait for traffic split to take effect
            await asyncio.sleep(30)
            
            # Get service URL for this stage
            service_url = await self.get_service_url(percentage)
            
            # Run load test if enabled
            if self.load_test_enabled:
                load_test_passed, load_results = await self.run_stage_load_test(stage, service_url)
                rollout_results.append({
                    'stage': stage_name,
                    'load_test_passed': load_test_passed,
                    'load_results': load_results
                })
                
                if not load_test_passed:
                    if self.auto_rollback:
                        await self.rollback_deployment(f"Load test failed for {stage_name}")
                    return False
            
            # Monitor stage health
            health_ok = await self.monitor_stage_health(stage, duration)
            if not health_ok:
                if self.auto_rollback:
                    await self.rollback_deployment(f"Health monitoring failed for {stage_name}")
                return False
            
            self.logger.info(f"✅ Stage {stage_name} completed successfully")
        
        # All stages completed successfully
        self.logger.info("✅ Progressive rollout completed successfully")
        self._log_rollout_summary(rollout_results, True)
        
        return True
    
    def _log_rollout_summary(self, results: List[Dict], overall_success: bool):
        """Log rollout summary to deployment report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅ COMPLETED" if overall_success else "❌ FAILED"
        
        summary = f"""
## 🎯 Progressive Rollout Summary

**Timestamp:** {timestamp}  
**Status:** {status}  
**Deployment:** {self.deployment_name}  
**Namespace:** {self.namespace}  
**Load Testing:** {'Enabled' if self.load_test_enabled else 'Disabled'}  
**Auto-rollback:** {'Enabled' if self.auto_rollback else 'Disabled'}  

### Rollout Stages

| Stage | Load Test | Status |
|-------|-----------|--------|
"""
        
        for result in results:
            stage_name = result['stage']
            load_test_status = "✅ PASSED" if result.get('load_test_passed', True) else "❌ FAILED"
            summary += f"| {stage_name} | {load_test_status} | Completed |\n"
        
        # Append to deployment report
        report_path = Path("deploy/deployment_report.md")
        if report_path.exists():
            with open(report_path, 'a') as f:
                f.write(summary)
        else:
            with open(report_path, 'w') as f:
                f.write(f"# Deployment Report\n{summary}")


async def main():
    """Main entry point for progressive rollout."""
    parser = argparse.ArgumentParser(description="Enhanced Progressive Rollout")
    parser.add_argument("--deployment", required=True,
                       help="Deployment name")
    parser.add_argument("--namespace", default="production",
                       help="Kubernetes namespace")
    parser.add_argument("--load-test", action="store_true",
                       help="Enable load testing at each stage")
    parser.add_argument("--auto-rollback-on-loadfail", action="store_true",
                       help="Auto-rollback on load test failure")
    parser.add_argument("--stages", type=str,
                       help="Custom rollout stages as JSON")
    
    args = parser.parse_args()
    
    # Create progressive rollout manager
    rollout = ProgressiveRollout(
        deployment_name=args.deployment,
        namespace=args.namespace,
        load_test_enabled=args.load_test,
        auto_rollback=args.auto_rollback_on_loadfail
    )
    
    # Override stages if provided
    if args.stages:
        try:
            custom_stages = json.loads(args.stages)
            rollout.rollout_stages = custom_stages
        except json.JSONDecodeError as e:
            print(f"❌ Invalid stages JSON: {e}")
            exit(1)
    
    try:
        # Execute progressive rollout
        success = await rollout.execute_progressive_rollout()
        
        if success:
            print("✅ Progressive rollout completed successfully")
            exit(0)
        else:
            print("❌ Progressive rollout failed")
            exit(1)
            
    except Exception as e:
        print(f"❌ Progressive rollout error: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
