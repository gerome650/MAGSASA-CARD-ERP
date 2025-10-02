#!/usr/bin/env python3
"""
Port Detection Utility for Chaos Engineering
Automatically detects which port the Flask service is running on.
"""

import argparse
import json
import os
import psutil
import requests
import socket
import subprocess
import sys
import time
from typing import List, Optional, Tuple


class PortDetector:
    """Detects the port where the Flask service is running."""
    
    def __init__(self, service_name: str = "python", process_pattern: str = "main.py"):
        self.service_name = service_name
        self.process_pattern = process_pattern
        self.common_ports = [8000, 5000, 5001, 3000, 8080, 8888]
        self.health_endpoint = "/api/health"
    
    def find_process_ports(self) -> List[int]:
        """Find ports used by processes matching our service pattern."""
        ports = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check if this is our Flask process
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if (self.service_name in proc.info['name'] and 
                            self.process_pattern in cmdline):
                            
                            # Get network connections for this process
                            connections = proc.connections(kind='inet')
                            for conn in connections:
                                if (conn.status == psutil.CONN_LISTEN and 
                                    conn.laddr.ip in ['127.0.0.1', '0.0.0.0', '::']):
                                    ports.append(conn.laddr.port)
                                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            print(f"Warning: Could not scan processes: {e}", file=sys.stderr)
        
        return list(set(ports))  # Remove duplicates
    
    def check_port_health(self, port: int, host: str = "localhost") -> Tuple[bool, Optional[dict]]:
        """Check if a service is healthy on the given port."""
        url = f"http://{host}:{port}{self.health_endpoint}"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return True, data
                except json.JSONDecodeError:
                    # Health endpoint exists but doesn't return JSON
                    return True, {"status": "healthy", "response": response.text[:100]}
            else:
                return False, {"status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
    
    def scan_common_ports(self, host: str = "localhost") -> List[Tuple[int, dict]]:
        """Scan common ports for Flask services."""
        healthy_services = []
        
        for port in self.common_ports:
            is_healthy, info = self.check_port_health(port, host)
            if is_healthy:
                healthy_services.append((port, info))
        
        return healthy_services
    
    def detect_flask_port(self, host: str = "localhost") -> Optional[Tuple[int, dict]]:
        """
        Detect the port where Flask service is running.
        Returns (port, health_info) if found, None otherwise.
        """
        print("🔍 Detecting Flask service port...", file=sys.stderr)
        
        # Method 1: Check processes
        process_ports = self.find_process_ports()
        if process_ports:
            print(f"   Found processes on ports: {process_ports}", file=sys.stderr)
            
            for port in process_ports:
                is_healthy, info = self.check_port_health(port, host)
                if is_healthy:
                    print(f"   ✅ Found healthy service on port {port}", file=sys.stderr)
                    return port, info
        
        # Method 2: Check environment variables
        env_port = os.getenv('APP_PORT') or os.getenv('FLASK_PORT')
        if env_port:
            try:
                port = int(env_port)
                print(f"   Checking environment port: {port}", file=sys.stderr)
                is_healthy, info = self.check_port_health(port, host)
                if is_healthy:
                    print(f"   ✅ Found healthy service on environment port {port}", file=sys.stderr)
                    return port, info
            except ValueError:
                pass
        
        # Method 3: Scan common ports
        print("   Scanning common ports...", file=sys.stderr)
        healthy_services = self.scan_common_ports(host)
        
        if healthy_services:
            # Prefer Flask-specific services
            for port, info in healthy_services:
                service_name = info.get('service', '').lower()
                if 'flask' in service_name or 'magsasa' in service_name:
                    print(f"   ✅ Found Flask service on port {port}", file=sys.stderr)
                    return port, info
            
            # Return first healthy service
            port, info = healthy_services[0]
            print(f"   ✅ Found service on port {port}", file=sys.stderr)
            return port, info
        
        print("   ❌ No healthy Flask service found", file=sys.stderr)
        return None
    
    def get_target_url(self, host: str = "localhost", 
                      fallback_port: int = 8000) -> Tuple[str, bool]:
        """
        Get the target URL for the Flask service.
        Returns (url, detected) where detected indicates if port was auto-detected.
        """
        result = self.detect_flask_port(host)
        
        if result:
            port, info = result
            return f"http://{host}:{port}", True
        else:
            print(f"   ⚠️  Using fallback port {fallback_port}", file=sys.stderr)
            return f"http://{host}:{fallback_port}", False


def main():
    """Main entry point for port detection utility."""
    parser = argparse.ArgumentParser(
        description="Detect Flask service port for chaos testing"
    )
    parser.add_argument("--host", default="localhost",
                       help="Target host (default: localhost)")
    parser.add_argument("--fallback-port", type=int, default=8000,
                       help="Fallback port if detection fails (default: 8000)")
    parser.add_argument("--service-name", default="python",
                       help="Service process name to look for (default: python)")
    parser.add_argument("--process-pattern", default="main.py",
                       help="Process command pattern to match (default: main.py)")
    parser.add_argument("--json", action="store_true",
                       help="Output result as JSON")
    parser.add_argument("--url-only", action="store_true",
                       help="Output only the URL")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress detection messages")
    
    args = parser.parse_args()
    
    # Redirect stderr to devnull if quiet
    if args.quiet:
        sys.stderr = open(os.devnull, 'w')
    
    detector = PortDetector(args.service_name, args.process_pattern)
    url, detected = detector.get_target_url(args.host, args.fallback_port)
    
    if args.url_only:
        print(url)
    elif args.json:
        result = {
            "url": url,
            "detected": detected,
            "host": args.host,
            "port": int(url.split(':')[-1]),
            "timestamp": time.time()
        }
        print(json.dumps(result, indent=2))
    else:
        status = "detected" if detected else "fallback"
        print(f"Target URL: {url} ({status})")
    
    # Exit with appropriate code
    sys.exit(0 if detected else 1)


if __name__ == "__main__":
    main()
