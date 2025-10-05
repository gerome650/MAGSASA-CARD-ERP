#!/usr/bin/env python3
"""
Fix API route prefixes in all route files
Remove duplicate /api/ prefixes since blueprints are already registered with /api prefix
"""

import os
import re


def fix_routes_in_file(filepath):
    """Fix API routes in a single file"""
    print(f"Fixing routes in {filepath}")

    with open(filepath) as f:
        content = f.read()

    # Replace @blueprint.route('/api/... with @blueprint.route('/...
    # This regex matches any blueprint name followed by .route('/api/
    pattern = r"(@\w+_bp\.route\(')(/api/)([^']+)('\s*,?\s*methods=)"
    replacement = r"\1/\3\4"

    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"  ✅ Fixed routes in {filepath}")
        return True
    else:
        print(f"  ℹ️  No changes needed in {filepath}")
        return False


def main():
    """Fix all route files"""
    route_files = [
        "src/routes/product.py",
        "src/routes/order.py",
        "src/routes/partner.py",
        "src/routes/category.py",
        "src/routes/supplier.py",
        "src/routes/partnership.py",
        "src/routes/financial.py",
        "src/routes/analytics.py",
        "src/routes/reports.py",
    ]

    fixed_count = 0
    for filepath in route_files:
        if os.path.exists(filepath):
            if fix_routes_in_file(filepath):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {filepath}")

    print(f"\n🎉 Fixed {fixed_count} route files")


if __name__ == "__main__":
    main()
