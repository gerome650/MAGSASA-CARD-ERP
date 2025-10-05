#!/usr/bin/env python3
"""
Script to add authorization decorators to all existing API endpoints in the AgSense ERP system.
This script will update all route files to include proper permission checks.
"""

import os
import re

# Define permission mappings for each module
PERMISSION_MAPPINGS = {
    "farmer.py": {
        "GET": "farmer_management_read",
        "POST": "farmer_management_create",
        "PUT": "farmer_management_update",
        "DELETE": "farmer_management_delete",
    },
    "product.py": {
        "GET": "product_catalog_read",
        "POST": "product_catalog_create",
        "PUT": "product_catalog_update",
        "DELETE": "product_catalog_delete",
    },
    "order.py": {
        "GET": "order_management_read",
        "POST": "order_management_create",
        "PUT": "order_management_update",
        "DELETE": "order_management_delete",
    },
    "partner.py": {
        "GET": "partner_network_read",
        "POST": "partner_network_create",
        "PUT": "partner_network_update",
        "DELETE": "partner_network_delete",
    },
    "partnership.py": {
        "GET": "partner_network_read",
        "POST": "partner_network_create",
        "PUT": "partner_network_update",
        "DELETE": "partner_network_delete",
    },
    "analytics.py": {
        "GET": "analytics_reports_read",
        "POST": "analytics_reports_create",
        "PUT": "analytics_reports_update",
        "DELETE": "analytics_reports_delete",
    },
    "financial.py": {
        "GET": "financial_reports_read",
        "POST": "financial_reports_create",
        "PUT": "financial_reports_update",
        "DELETE": "financial_reports_delete",
    },
    "reports.py": {
        "GET": "analytics_reports_read",
        "POST": "analytics_reports_create",
        "PUT": "analytics_reports_update",
        "DELETE": "analytics_reports_delete",
    },
    "category.py": {
        "GET": "product_catalog_read",
        "POST": "product_catalog_create",
        "PUT": "product_catalog_update",
        "DELETE": "product_catalog_delete",
    },
    "supplier.py": {
        "GET": "product_catalog_read",
        "POST": "product_catalog_create",
        "PUT": "product_catalog_update",
        "DELETE": "product_catalog_delete",
    },
    "farmer_orders.py": {
        "GET": "order_management_read",
        "POST": "order_management_create",
        "PUT": "order_management_update",
        "DELETE": "order_management_delete",
    },
    "dashboard.py": {"GET": "dashboard_read"},
}


def add_auth_import(file_path):
    """Add authentication import to the file if not already present"""
    with open(file_path) as f:
        content = f.read()

    # Check if auth import already exists
    if "from src.routes.auth import" in content:
        return content

    # Find the last import line and add auth import after it
    lines = content.split("\n")
    import_line_index = -1

    for i, line in enumerate(lines):
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            import_line_index = i

    if import_line_index >= 0:
        lines.insert(
            import_line_index + 1,
            "from src.routes.auth import require_permission, require_auth",
        )
        return "\n".join(lines)

    return content


def add_auth_decorators(file_path, filename):
    """Add authentication decorators to route functions"""
    if filename not in PERMISSION_MAPPINGS:
        return

    with open(file_path) as f:
        content = f.read()

    # Add auth import
    content = add_auth_import(file_path)

    # Find all route definitions and add decorators
    route_pattern = r"@\w+_bp\.route\([^)]+methods=\[([^\]]+)\][^)]*\)\s*\ndef\s+(\w+)"

    def replace_route(match):
        methods_str = match.group(1)
        match.group(2)

        # Extract HTTP methods
        methods = [method.strip().strip("\"'") for method in methods_str.split(",")]

        # Determine permission based on HTTP method
        permission = None
        for method in methods:
            if method.upper() in PERMISSION_MAPPINGS[filename]:
                permission = PERMISSION_MAPPINGS[filename][method.upper()]
                break

        if not permission:
            permission = PERMISSION_MAPPINGS[filename].get("GET", "dashboard_read")

        # Build the replacement with decorator
        original_route = match.group(0)

        # Check if decorator already exists
        if "@require_permission" in original_route or "@require_auth" in original_route:
            return original_route

        # Add decorator before the function definition
        lines = original_route.split("\n")
        func_def_line = None
        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                func_def_line = i
                break

        if func_def_line is not None:
            lines.insert(func_def_line, f"@require_permission('{permission}')")
            return "\n".join(lines)

        return original_route

    # Apply the replacements
    updated_content = re.sub(route_pattern, replace_route, content, flags=re.MULTILINE)

    # Write back to file
    with open(file_path, "w") as f:
        f.write(updated_content)

    print(f"Updated {filename} with authentication decorators")


def main():
    """Main function to process all route files"""
    routes_dir = "/home/ubuntu/agsense_erp/src/routes"

    if not os.path.exists(routes_dir):
        print(f"Routes directory not found: {routes_dir}")
        return

    # Process each route file
    for filename in os.listdir(routes_dir):
        if (
            filename.endswith(".py")
            and filename != "__init__.py"
            and filename != "auth.py"
        ):
            file_path = os.path.join(routes_dir, filename)
            print(f"Processing {filename}...")
            add_auth_decorators(file_path, filename)

    print("Authentication decorators added to all route files!")


if __name__ == "__main__":
    main()
