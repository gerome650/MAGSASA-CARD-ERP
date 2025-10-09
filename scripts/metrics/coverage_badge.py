#!/usr/bin/env python3
"""
🏷️ Coverage Badge Generator

Generates SVG coverage badges and updates README with:
- Dynamic coverage percentage badges
- Color-coded coverage levels
- Integration with coverage history
- README auto-update functionality

Usage:
    python scripts/metrics/coverage_badge.py --update-readme
    python scripts/metrics/coverage_badge.py --generate-badge --coverage 87.5
    python scripts/metrics/coverage_badge.py --badge-file coverage.svg
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class CoverageBadgeGenerator:
    """Generate coverage badges and update documentation."""

    def __init__(self, verbose: bool = False):
        """Initialize badge generator.

        Args:
            verbose: Whether to enable verbose logging
        """
        self.verbose = verbose
        self.repo_root = Path(__file__).parent.parent.parent
        self.badges_dir = self.repo_root / "badges"
        self.coverage_history_file = self.repo_root / ".ci" / "coverage_history.json"
        self.readme_file = self.repo_root / "README.md"

        # Create badges directory
        self.badges_dir.mkdir(exist_ok=True)

    def get_coverage_color(self, coverage: float) -> str:
        """Get color for coverage percentage.

        Args:
            coverage: Coverage percentage (0-100)

        Returns:
            Hex color code
        """
        if coverage >= 95:
            return "#4c1"  # Bright green
        elif coverage >= 90:
            return "#97ca00"  # Green
        elif coverage >= 80:
            return "#dfb317"  # Yellow
        elif coverage >= 70:
            return "#fe7d37"  # Orange
        else:
            return "#e05d44"  # Red

    def get_coverage_status(self, coverage: float) -> str:
        """Get status text for coverage percentage.

        Args:
            coverage: Coverage percentage (0-100)

        Returns:
            Status text
        """
        if coverage >= 95:
            return "excellent"
        elif coverage >= 90:
            return "good"
        elif coverage >= 80:
            return "acceptable"
        elif coverage >= 70:
            return "needs improvement"
        else:
            return "critical"

    def get_latest_coverage(self) -> float | None:
        """Get the latest coverage from history file.

        Returns:
            Latest coverage percentage or None if not available
        """
        if not self.coverage_history_file.exists():
            return None

        try:
            with open(self.coverage_history_file) as f:
                data = json.load(f)

            entries = data.get("entries", [])
            if not entries:
                return None

            # Sort by timestamp and get the latest
            entries.sort(key=lambda x: x.get("timestamp", ""))
            latest_entry = entries[-1]
            return latest_entry.get("coverage", None)

        except (OSError, json.JSONDecodeError, KeyError) as e:
            if self.verbose:
                logger.warning(f"Could not read coverage history: {e}")
            return None

    def generate_svg_badge(self, coverage: float, label: str = "coverage") -> str:
        """Generate SVG badge for coverage.

        Args:
            coverage: Coverage percentage (0-100)
            label: Badge label text

        Returns:
            SVG badge content
        """
        color = self.get_coverage_color(coverage)
        self.get_coverage_status(coverage)

        # Calculate badge dimensions
        label_width = len(label) * 6 + 10
        value_text = f"{coverage:.1f}%"
        value_width = len(value_text) * 6 + 10
        total_width = label_width + value_width

        # SVG template
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h{label_width}v20H0z"/>
    <path fill="{color}" d="M{label_width} 0h{value_width}v20H{label_width}z"/>
    <path fill="url(#b)" d="M0 0h{total_width}v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_width/2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width/2}" y="14">{label}</text>
    <text x="{label_width + value_width/2}" y="15" fill="#010101" fill-opacity=".3">{value_text}</text>
    <text x="{label_width + value_width/2}" y="14">{value_text}</text>
  </g>
</svg>"""

        return svg_content

    def save_badge(self, svg_content: str, filename: str = "coverage.svg") -> bool:
        """Save SVG badge to file.

        Args:
            svg_content: SVG badge content
            filename: Badge filename

        Returns:
            True if successful
        """
        try:
            badge_file = self.badges_dir / filename
            with open(badge_file, "w") as f:
                f.write(svg_content)

            if self.verbose:
                logger.info(f"Badge saved: {badge_file}")
            return True

        except OSError as e:
            logger.error(f"Failed to save badge: {e}")
            return False

    def update_readme_badge(self, coverage: float) -> bool:
        """Update coverage badge in README.md.

        Args:
            coverage: Coverage percentage

        Returns:
            True if successful
        """
        if not self.readme_file.exists():
            if self.verbose:
                logger.warning("README.md not found, skipping badge update")
            return False

        try:
            # Read README content
            with open(self.readme_file) as f:
                content = f.read()

            # Generate new badge SVG
            self.generate_svg_badge(coverage)

            # Create badge markdown (using shields.io style)
            color = self.get_coverage_color(coverage)
            self.get_coverage_status(coverage)

            # Convert hex color to shields.io format (remove #)
            shields_color = color.lstrip("#")

            badge_markdown = f"[![Coverage](https://img.shields.io/badge/coverage-{coverage:.1f}%25-{shields_color}?style=flat-square)]({self.badges_dir.name}/coverage.svg)"

            # Pattern to find existing coverage badge
            badge_pattern = r"\[!\[Coverage\][^\]]*\]\([^)]*\)"

            if re.search(badge_pattern, content):
                # Replace existing badge
                new_content = re.sub(badge_pattern, badge_markdown, content)
            else:
                # Add badge at the top after title
                lines = content.split("\n")
                insert_index = 0

                # Find a good place to insert (after title, before first section)
                for i, line in enumerate(lines):
                    if line.startswith("# ") and i < 10:  # Main title
                        insert_index = i + 1
                        break

                lines.insert(insert_index, badge_markdown)
                lines.insert(insert_index + 1, "")  # Empty line
                new_content = "\n".join(lines)

            # Write updated content
            with open(self.readme_file, "w") as f:
                f.write(new_content)

            if self.verbose:
                logger.info(f"Updated README.md with coverage badge: {coverage:.1f}%")
            return True

        except OSError as e:
            logger.error(f"Failed to update README badge: {e}")
            return False

    def generate_badge_report(self, coverage: float) -> str:
        """Generate a badge generation report.

        Args:
            coverage: Coverage percentage

        Returns:
            Formatted report string
        """
        color = self.get_coverage_color(coverage)
        status = self.get_coverage_status(coverage)

        report_lines = [
            "🏷️ Coverage Badge Report",
            "=" * 30,
            "",
            f"📊 Coverage: {coverage:.1f}%",
            f"🎨 Color: {color}",
            f"📈 Status: {status.title()}",
            "📁 Badge saved: badges/coverage.svg",
            f"📝 README updated: {'✅' if self.readme_file.exists() else '❌'}",
            "",
            f"📅 Generated: {Path().cwd()}",
            "=" * 30,
        ]

        return "\n".join(report_lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Coverage badge generator")
    parser.add_argument(
        "--update-readme", action="store_true", help="Update README with coverage badge"
    )
    parser.add_argument(
        "--generate-badge", action="store_true", help="Generate coverage badge"
    )
    parser.add_argument(
        "--coverage",
        type=float,
        help="Coverage percentage (auto-detected if not provided)",
    )
    parser.add_argument(
        "--badge-file",
        default="coverage.svg",
        help="Badge filename (default: coverage.svg)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    generator = CoverageBadgeGenerator(verbose=args.verbose)

    try:
        # Get coverage value
        if args.coverage is not None:
            coverage = args.coverage
        else:
            coverage = generator.get_latest_coverage()
            if coverage is None:
                print(
                    "❌ No coverage data available. Provide --coverage or ensure coverage history exists."
                )
                sys.exit(1)

        if generator.verbose:
            logger.info(f"Using coverage: {coverage:.1f}%")

        success = True

        # Generate badge if requested
        if args.generate_badge or args.update_readme:
            svg_badge = generator.generate_svg_badge(coverage)
            if not generator.save_badge(svg_badge, args.badge_file):
                success = False

        # Update README if requested
        if args.update_readme and not generator.update_readme_badge(coverage):
            success = False

        # Show report if verbose
        if args.verbose:
            report = generator.generate_badge_report(coverage)
            print(report)

        if success:
            print(f"✅ Coverage badge generated: {coverage:.1f}%")
            sys.exit(0)
        else:
            print("❌ Some operations failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Badge generation failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
