#!/usr/bin/env python3
"""
Chaos Dependency Sentinel - Stage 7.2
Automatically detects and manages missing dependencies in chaos validation scripts.
"""

import argparse
import ast
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencySentinel:
    """Automatically detects and manages dependencies for chaos scripts."""
    
    # Standard library modules that don't need to be installed
    STDLIB_MODULES = {
        'argparse', 'asyncio', 'collections', 'dataclasses', 'datetime', 
        'functools', 'io', 'json', 'logging', 'os', 'pathlib', 'queue',
        're', 'shutil', 'socket', 'statistics', 'subprocess', 'sys', 'tempfile',
        'threading', 'time', 'typing', 'unittest', 'urllib', 'uuid', 'warnings',
        'abc', 'copy', 'csv', 'enum', 'hashlib', 'inspect', 'itertools', 'math',
        'operator', 'pickle', 'random', 'string', 'struct', 'traceback',
        'ast', 'glob', 'sqlite3', 'signal', 'shlex', 'urllib3', 'email',
        'http', 'html', 'xml', 'multiprocessing', 'concurrent', 'base64',
        'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'configparser',
    }
    
    # Internal project modules (part of the codebase, not external packages)
    INTERNAL_MODULES = {
        'alerts', 'anomaly_strategies', 'data_collector', 'dashboards',
        'incident_analyzer', 'incident_reporter', 'insight_engine',
        'integrations', 'notifier', 'observability', 'pagerduty_notifier',
        'postmortem_generator', 'remediation_advisor', 'slack_bot',
        'test_workflow', 'main', 'database', 'models', 'routes',
        'config', 'utils', 'helpers', 'services',
    }
    
    # Known package mappings (import name -> package name)
    PACKAGE_MAPPINGS = {
        'aiohttp': 'aiohttp>=3.9.0',
        'yaml': 'PyYAML>=6.0.2',
        'requests': 'requests>=2.31.0',
        'pytest': 'pytest>=7.4.0',
        'flask': 'flask>=2.3.0',
        'numpy': 'numpy>=1.21.0',
        'scipy': 'scipy>=1.7.0',
        'prometheus_client': 'prometheus-client>=0.19.0',
        'opentelemetry': 'opentelemetry-api>=1.21.0',
        'tabulate': 'tabulate>=0.9.0',
    }
    
    def __init__(self, target_dirs: List[str] = None, requirements_files: List[str] = None):
        self.target_dirs = target_dirs or ['deploy', 'scripts', 'observability']
        self.requirements_files = requirements_files or ['requirements.txt', 'observability/observability_requirements.txt']
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [%(levelname)s] - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def extract_imports_from_file(self, file_path: str) -> Set[str]:
        """Extract all imports from a Python file using AST."""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get top-level module name
                        module = alias.name.split('.')[0]
                        imports.add(module)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get top-level module name
                        module = node.module.split('.')[0]
                        imports.add(module)
                        
        except Exception as e:
            self.logger.warning(f"Failed to parse {file_path}: {e}")
        
        return imports
    
    def scan_directory_for_imports(self, directory: str) -> Dict[str, Set[str]]:
        """Scan a directory for all Python imports."""
        all_imports = {}
        
        dir_path = Path(directory)
        if not dir_path.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return all_imports
        
        for py_file in dir_path.rglob('*.py'):
            # Skip __pycache__ and venv
            if '__pycache__' in str(py_file) or 'venv' in str(py_file):
                continue
                
            imports = self.extract_imports_from_file(str(py_file))
            if imports:
                all_imports[str(py_file)] = imports
        
        return all_imports
    
    def load_requirements(self, requirements_file: str) -> Set[str]:
        """Load existing requirements from a requirements file."""
        requirements = set()
        
        if not os.path.exists(requirements_file):
            self.logger.warning(f"Requirements file not found: {requirements_file}")
            return requirements
        
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Extract package name (before any version specifier)
                    package = re.split(r'[>=<~!]', line)[0].strip()
                    # Normalize package name (convert - to _)
                    normalized = package.replace('-', '_').lower()
                    requirements.add(normalized)
                    
        except Exception as e:
            self.logger.error(f"Failed to read {requirements_file}: {e}")
        
        return requirements
    
    def find_missing_dependencies(self) -> Tuple[Dict[str, List[str]], Set[str]]:
        """
        Find all missing dependencies across target directories.
        
        Returns:
            Tuple of (missing_deps_by_file, all_missing_packages)
        """
        self.logger.info("🔍 Scanning for dependencies...")
        
        # Scan all target directories
        all_imports = {}
        for target_dir in self.target_dirs:
            imports = self.scan_directory_for_imports(target_dir)
            all_imports.update(imports)
        
        # Load existing requirements
        existing_requirements = set()
        for req_file in self.requirements_files:
            reqs = self.load_requirements(req_file)
            existing_requirements.update(reqs)
        
        # Find missing dependencies
        missing_by_file = {}
        all_missing = set()
        
        for file_path, imports in all_imports.items():
            missing = []
            
            for imp in imports:
                # Skip standard library modules
                if imp in self.STDLIB_MODULES:
                    continue
                
                # Skip internal project modules
                if imp in self.INTERNAL_MODULES:
                    continue
                
                # Normalize import name
                normalized_imp = imp.replace('-', '_').lower()
                
                # Check if already in requirements
                if normalized_imp not in existing_requirements:
                    missing.append(imp)
                    all_missing.add(imp)
            
            if missing:
                missing_by_file[file_path] = missing
        
        return missing_by_file, all_missing
    
    def get_package_spec(self, module_name: str) -> str:
        """Get the package specification for a module."""
        # Check if we have a known mapping
        if module_name in self.PACKAGE_MAPPINGS:
            return self.PACKAGE_MAPPINGS[module_name]
        
        # For unknown packages, use a conservative version spec
        # Convert module name to package name (usually the same)
        package_name = module_name.replace('_', '-')
        return f"{package_name}>=1.0.0"
    
    def auto_fix_requirements(self, missing_packages: Set[str], 
                              dry_run: bool = False) -> bool:
        """
        Automatically add missing packages to requirements files.
        
        Args:
            missing_packages: Set of missing package names
            dry_run: If True, only show what would be added
            
        Returns:
            True if successful, False otherwise
        """
        if not missing_packages:
            self.logger.info("✅ No missing dependencies found")
            return True
        
        self.logger.info(f"📦 Found {len(missing_packages)} missing dependencies")
        
        # Categorize packages by requirements file
        chaos_packages = {'aiohttp', 'pyyaml', 'requests'}
        
        for package in missing_packages:
            spec = self.get_package_spec(package)
            
            # Determine which requirements file to update
            if package.lower() in chaos_packages:
                target_file = 'requirements.txt'
            else:
                target_file = 'observability/observability_requirements.txt'
            
            self.logger.info(f"   {'[DRY RUN]' if dry_run else '+'} {spec} -> {target_file}")
            
            if not dry_run:
                self._add_to_requirements(spec, target_file)
        
        return True
    
    def _add_to_requirements(self, package_spec: str, requirements_file: str):
        """Add a package to a requirements file."""
        try:
            # Read existing content
            content = []
            if os.path.exists(requirements_file):
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    content = f.readlines()
            
            # Check if package is already there (shouldn't be, but just in case)
            package_name = package_spec.split('>=')[0].split('==')[0].strip()
            already_exists = any(
                package_name.lower() in line.lower() 
                for line in content 
                if not line.strip().startswith('#')
            )
            
            if already_exists:
                self.logger.debug(f"   Package {package_name} already in {requirements_file}")
                return
            
            # Add the new package
            with open(requirements_file, 'a', encoding='utf-8') as f:
                # Add a newline if file doesn't end with one
                if content and not content[-1].endswith('\n'):
                    f.write('\n')
                
                # Add comment header if this is a new section
                if not any('Chaos' in line for line in content):
                    f.write('\n# Chaos Engineering Dependencies (Auto-added by Sentinel)\n')
                
                f.write(f'{package_spec}\n')
            
            self.logger.info(f"   ✅ Added {package_spec} to {requirements_file}")
            
        except Exception as e:
            self.logger.error(f"   ❌ Failed to add {package_spec} to {requirements_file}: {e}")
    
    def install_missing_packages(self, missing_packages: Set[str], 
                                 dry_run: bool = False) -> bool:
        """
        Install missing packages using pip.
        
        Args:
            missing_packages: Set of missing package names
            dry_run: If True, only show what would be installed
            
        Returns:
            True if successful, False otherwise
        """
        if not missing_packages:
            return True
        
        self.logger.info("📥 Installing missing packages...")
        
        for package in missing_packages:
            spec = self.get_package_spec(package)
            
            if dry_run:
                self.logger.info(f"   [DRY RUN] Would install: {spec}")
            else:
                self.logger.info(f"   Installing: {spec}")
                try:
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', spec],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.logger.info(f"   ✅ Installed {spec}")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"   ❌ Failed to install {spec}: {e.stderr}")
                    return False
        
        return True
    
    def generate_report(self, missing_by_file: Dict[str, List[str]], 
                       output_file: str = "reports/dependency_sentinel_report.md"):
        """Generate a markdown report of findings."""
        report = f"""# Chaos Dependency Sentinel Report

**Generated:** {Path(__file__).name}
**Scan Directories:** {', '.join(self.target_dirs)}
**Requirements Files:** {', '.join(self.requirements_files)}

## Summary

- **Total Files Scanned:** {len(missing_by_file)}
- **Files with Missing Dependencies:** {sum(1 for deps in missing_by_file.values() if deps)}
- **Total Missing Dependencies:** {len(set(dep for deps in missing_by_file.values() for dep in deps))}

## Missing Dependencies by File

"""
        
        if not any(missing_by_file.values()):
            report += "✅ **No missing dependencies found!**\n"
        else:
            for file_path, missing_deps in sorted(missing_by_file.items()):
                if missing_deps:
                    report += f"### `{file_path}`\n\n"
                    for dep in sorted(missing_deps):
                        spec = self.get_package_spec(dep)
                        report += f"- `{spec}`\n"
                    report += "\n"
        
        report += """
## Recommendations

1. Run with `--fix` to automatically add missing dependencies to requirements files
2. Run with `--install` to automatically install missing packages
3. Review auto-added dependencies and adjust versions as needed
4. Consider pinning dependencies to specific versions for reproducibility

## Auto-Fix Command

```bash
python scripts/chaos_dependency_sentinel.py --fix --install
```
"""
        
        # Save report
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"📄 Report saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")


def main():
    """Main entry point for dependency sentinel."""
    parser = argparse.ArgumentParser(
        description="Chaos Dependency Sentinel - Auto-detect and manage missing dependencies"
    )
    parser.add_argument('--scan-dirs', nargs='+',
                       default=['deploy', 'scripts', 'observability'],
                       help='Directories to scan for Python files')
    parser.add_argument('--requirements', nargs='+',
                       default=['requirements.txt', 'observability/observability_requirements.txt'],
                       help='Requirements files to check against')
    parser.add_argument('--fix', action='store_true',
                       help='Automatically add missing dependencies to requirements files')
    parser.add_argument('--install', action='store_true',
                       help='Automatically install missing packages')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--report', type=str,
                       default='reports/dependency_sentinel_report.md',
                       help='Output file for report')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🤖 Chaos Dependency Sentinel - Stage 7.2")
    print("=" * 60)
    
    # Create sentinel
    sentinel = DependencySentinel(
        target_dirs=args.scan_dirs,
        requirements_files=args.requirements
    )
    
    # Find missing dependencies
    missing_by_file, all_missing = sentinel.find_missing_dependencies()
    
    # Generate report
    sentinel.generate_report(missing_by_file, args.report)
    
    # Print summary
    print(f"\n📊 Scan Results:")
    print(f"   Files scanned: {len(missing_by_file)}")
    print(f"   Missing dependencies: {len(all_missing)}")
    
    if all_missing:
        print(f"\n⚠️  Missing Dependencies:")
        for dep in sorted(all_missing):
            print(f"   - {sentinel.get_package_spec(dep)}")
    
    # Auto-fix if requested
    if args.fix and all_missing:
        print(f"\n🔧 Auto-fixing requirements files...")
        sentinel.auto_fix_requirements(all_missing, dry_run=args.dry_run)
    
    # Install if requested
    if args.install and all_missing:
        print(f"\n📥 Installing missing packages...")
        if not sentinel.install_missing_packages(all_missing, dry_run=args.dry_run):
            print("❌ Package installation failed")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    if all_missing and not args.fix:
        print("⚠️  Missing dependencies detected!")
        print("   Run with --fix to automatically update requirements files")
        print("   Run with --install to automatically install packages")
        sys.exit(1)
    else:
        print("✅ All dependencies resolved!")
        sys.exit(0)


if __name__ == "__main__":
    main()

