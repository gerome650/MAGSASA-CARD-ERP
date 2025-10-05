#!/usr/bin/env python3
"""
Email notification system for CI/CD preflight failures.
Sends structured HTML reports with failure details and next steps.
"""

import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailNotifier:
    """Handles email notifications for CI/CD failures."""

    def __init__(self):
        """Initialize email notifier with SMTP settings."""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASS")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.alert_email = os.getenv("ALERT_EMAIL")

        if not all([self.smtp_user, self.smtp_password, self.alert_email]):
            raise ValueError(
                "SMTP_USER, SMTP_PASS, and ALERT_EMAIL environment variables are required"
            )

    def _generate_html_report(
        self,
        branch: str,
        commit_sha: str,
        failing_checks: list[str],
        logs_url: str | None = None,
        pr_url: str | None = None,
    ) -> str:
        """Generate HTML report for email."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        checks_html = ""
        for check in failing_checks:
            checks_html += f"""
            <li class="check-item">
                <span class="check-icon">❌</span>
                <span class="check-name">{check}</span>
            </li>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>CI/CD Preflight Failure Report</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #dc3545;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #dc3545;
                    margin: 0;
                    font-size: 24px;
                }}
                .header .subtitle {{
                    color: #6c757d;
                    margin-top: 5px;
                    font-size: 14px;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .info-item {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #dc3545;
                }}
                .info-item h3 {{
                    margin: 0 0 8px 0;
                    color: #495057;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .info-item p {{
                    margin: 0;
                    font-size: 16px;
                    font-weight: 500;
                    color: #212529;
                }}
                .checks-section {{
                    margin-bottom: 30px;
                }}
                .checks-section h2 {{
                    color: #dc3545;
                    font-size: 18px;
                    margin-bottom: 15px;
                }}
                .checks-list {{
                    list-style: none;
                    padding: 0;
                    margin: 0;
                }}
                .check-item {{
                    display: flex;
                    align-items: center;
                    padding: 12px;
                    background: #fff5f5;
                    border: 1px solid #fed7d7;
                    border-radius: 6px;
                    margin-bottom: 8px;
                }}
                .check-icon {{
                    margin-right: 12px;
                    font-size: 18px;
                }}
                .check-name {{
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 14px;
                    color: #2d3748;
                }}
                .next-steps {{
                    background: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 6px;
                    padding: 20px;
                    margin-bottom: 30px;
                }}
                .next-steps h2 {{
                    color: #1976d2;
                    font-size: 18px;
                    margin-top: 0;
                    margin-bottom: 15px;
                }}
                .next-steps ol {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .next-steps li {{
                    margin-bottom: 8px;
                    color: #424242;
                }}
                .code {{
                    background: #f1f3f4;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 13px;
                    color: #3c4043;
                    display: inline-block;
                    margin: 2px 0;
                }}
                .links {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                }}
                .links a {{
                    display: inline-block;
                    margin: 0 10px;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 500;
                }}
                .links a:hover {{
                    background: #0056b3;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                    color: #6c757d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 CI/CD Preflight Failure</h1>
                    <div class="subtitle">Automated Build Quality Check Failed</div>
                </div>

                <div class="info-grid">
                    <div class="info-item">
                        <h3>Branch</h3>
                        <p>{branch}</p>
                    </div>
                    <div class="info-item">
                        <h3>Commit SHA</h3>
                        <p>{commit_sha[:8]}</p>
                    </div>
                    <div class="info-item">
                        <h3>Failure Time</h3>
                        <p>{timestamp}</p>
                    </div>
                    <div class="info-item">
                        <h3>Failed Checks</h3>
                        <p>{len(failing_checks)} check(s)</p>
                    </div>
                </div>

                <div class="checks-section">
                    <h2>Failed Checks</h2>
                    <ul class="checks-list">
                        {checks_html}
                    </ul>
                </div>

                <div class="next-steps">
                    <h2>Next Steps</h2>
                    <ol>
                        <li>Review the failing checks listed above</li>
                        <li>Fix the issues locally using:
                            <br><span class="code">python -m ruff check . --fix</span>
                            <br><span class="code">python -m black .</span>
                            <br><span class="code">python -m mypy .</span>
                        </li>
                        <li>Run the preflight checks again:
                            <br><span class="code">make ci-preflight</span>
                        </li>
                        <li>Commit and push your fixes</li>
                    </ol>
                </div>

                <div class="links">
                    {f'<a href="{logs_url}">View Detailed Logs</a>' if logs_url else ''}
                    {f'<a href="{pr_url}">View Pull Request</a>' if pr_url else ''}
                </div>

                <div class="footer">
                    <p>This is an automated message from the MAGSASA-CARD-ERP CI/CD system.</p>
                    <p>For questions or issues, contact the development team.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    def send_preflight_failure(
        self,
        branch: str,
        commit_sha: str,
        failing_checks: list[str],
        logs_url: str | None = None,
        pr_url: str | None = None,
    ) -> bool:
        """
        Send email notification about preflight failure.

        Args:
            branch: Git branch name
            commit_sha: Git commit SHA
            failing_checks: List of failing check descriptions
            logs_url: Optional URL to logs
            pr_url: Optional URL to pull request

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 CI/CD Preflight Failed - {branch}"
            msg["From"] = self.from_email
            msg["To"] = self.alert_email

            # Generate HTML content
            html_content = self._generate_html_report(
                branch=branch,
                commit_sha=commit_sha,
                failing_checks=failing_checks,
                logs_url=logs_url,
                pr_url=pr_url,
            )

            # Create plain text version
            text_content = f"""
CI/CD Preflight Failure Report

Branch: {branch}
Commit: {commit_sha[:8]}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
Failed Checks: {len(failing_checks)}

Failed Checks:
{chr(10).join(f"- {check}" for check in failing_checks)}

Next Steps:
1. Review the failing checks listed above
2. Fix the issues locally using the provided commands
3. Run the preflight checks again: make ci-preflight
4. Commit and push your fixes

For detailed logs and more information, check the CI/CD dashboard.
            """

            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print("✅ Email notification sent successfully")
            return True

        except Exception as e:
            print(f"❌ Error sending email notification: {e}")
            return False


def main():
    """CLI interface for email notifications."""
    if len(sys.argv) < 4:
        print(
            "Usage: python notify_email.py <branch> <commit_sha> <failing_check1> [failing_check2] ..."
        )
        print(
            "Example: python notify_email.py main abc123 'Ruff linting failed' 'Type checking failed'"
        )
        sys.exit(1)

    branch = sys.argv[1]
    commit_sha = sys.argv[2]
    failing_checks = sys.argv[3:]

    try:
        notifier = EmailNotifier()
        success = notifier.send_preflight_failure(
            branch=branch,
            commit_sha=commit_sha,
            failing_checks=failing_checks,
            logs_url=os.getenv("CI_LOGS_URL"),
            pr_url=os.getenv("PR_URL"),
        )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
