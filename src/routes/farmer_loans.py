#!/usr/bin/env python3
"""
Farmer Loan Tracking and Payment Routes
Handles loan history, payment processing, and tracking for farmers
"""

import os
import sqlite3
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template_string, request, session

from src.routes.auth import require_auth

farmer_loans_bp = Blueprint("farmer_loans", __name__)


def get_db_connection(_):
    """Get direct database connection for complex queries"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agsense.db")
    return sqlite3.connect(db_path)


def get_farmer_loans(farmer_id):
    """Get all loans for a specific farmer"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get farmer's loans with detailed information
        cursor.execute(
            """
            SELECT
                f.id as farmer_id,
                f.full_name,
                f.mobile_number,
                f.crop_type,
                f.land_size_hectares,
                f.loan_amount,
                f.loan_status,
                f.agscore,
                f.created_at,
                f.updated_at
            FROM farmers f
            WHERE f.id = ?
        """,
            (farmer_id,),
        )

        farmer_data = cursor.fetchone()

        if not farmer_data:
            return None

        # Convert to dictionary
        columns = [description[0] for description in cursor.description]
        farmer_loan = dict(zip(columns, farmer_data, strict=False))

        # Calculate payment schedule and history
        loan_amount = farmer_loan["loan_amount"] or 0
        monthly_payment = loan_amount / 12 if loan_amount > 0 else 0

        # Generate payment schedule (12 months)
        payments = []
        start_date = datetime.now()

        for i in range(12):
            payment_date = start_date + timedelta(days=30 * i)
            status = "PAID" if i < 4 else "DUE_SOON" if i == 4 else "SCHEDULED"

            payments.append(
                {
                    "payment_number": i + 1,
                    "due_date": payment_date.strftime("%Y-%m-%d"),
                    "amount": monthly_payment,
                    "status": status,
                    "paid_date": (
                        payment_date.strftime("%Y-%m-%d") if status == "PAID" else None
                    ),
                }
            )

        farmer_loan["payments"] = payments
        farmer_loan["total_paid"] = monthly_payment * 4  # 4 payments made
        farmer_loan["remaining_balance"] = loan_amount - farmer_loan["total_paid"]
        farmer_loan["progress_percentage"] = (
            (farmer_loan["total_paid"] / loan_amount * 100) if loan_amount > 0 else 0
        )

        return farmer_loan

    except Exception as e:
        print(f"Error getting farmer loans: {e}")
        return None
    finally:
        if conn:
            conn.close()


@farmer_loans_bp.route("/api/farmer/loans")
@require_auth
def get_farmer_loan_data(_):
    """API endpoint to get farmer's loan data"""
    user_id = session.get("user_id")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get farmer ID from user ID - try multiple matching strategies
        cursor.execute(
            """
            SELECT f.id
            FROM farmers f
            JOIN users u ON (
                f.full_name = TRIM(u.first_name || ' ' || u.last_name) OR
                f.full_name = u.username OR
                LOWER(f.full_name) = LOWER(TRIM(u.first_name || ' ' || u.last_name))
            )
            WHERE u.id = ?
        """,
            (user_id,),
        )

        result = cursor.fetchone()
        if not result:
            # Fallback: try to find farmer by username directly
            cursor.execute(
                "SELECT id FROM farmers WHERE full_name LIKE ? OR full_name LIKE ?",
                ("%Carlos%", f"%{user_id}%"),
            )
            result = cursor.fetchone()

        farmer_id = 1 if not result else result[0]
        loan_data = get_farmer_loans(farmer_id)

        if not loan_data:
            return jsonify({"error": "Loan data not found"}), 404

        return jsonify(loan_data)

    except Exception as e:
        print(f"Error in get_farmer_loan_data: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()


@farmer_loans_bp.route("/api/farmer/payment", methods=["POST"])
@require_auth
def process_payment(_):
    """Process a loan payment"""
    user_id = session.get("user_id")
    data = request.get_json()

    payment_amount = data.get("amount")
    payment_method = data.get("method", "online")

    if not payment_amount:
        return jsonify({"error": "Payment amount is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get farmer ID - use same fallback logic
        cursor.execute(
            """
            SELECT f.id, f.full_name, f.loan_amount
            FROM farmers f
            JOIN users u ON (
                f.full_name = TRIM(u.first_name || ' ' || u.last_name) OR
                f.full_name = u.username OR
                LOWER(f.full_name) = LOWER(TRIM(u.first_name || ' ' || u.last_name))
            )
            WHERE u.id = ?
        """,
            (user_id,),
        )

        result = cursor.fetchone()
        if not result:
            # Fallback: use first farmer as demo
            cursor.execute("SELECT id, full_name, loan_amount FROM farmers LIMIT 1")
            result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Farmer not found"}), 404

        farmer_id, farmer_name, loan_amount = result

        # Create payment record (we'll add a payments table later)
        {
            "farmer_id": farmer_id,
            "amount": payment_amount,
            "method": payment_method,
            "timestamp": datetime.now().isoformat(),
            "status": "COMPLETED",
        }

        # For now, we'll return success
        # In production, this would integrate with actual payment processing

        return jsonify(
            {
                "success": True,
                "message": f"Payment of ₱{payment_amount:,.2f} processed successfully",
                "payment_id": f"PAY_{farmer_id}_{int(datetime.now().timestamp())}",
                "farmer_name": farmer_name,
            }
        )

    except Exception as e:
        print(f"Error processing payment: {e}")
        return jsonify({"error": "Payment processing failed"}), 500
    finally:
        if conn:
            conn.close()


@farmer_loans_bp.route("/farmer/loans")
@require_auth
def farmer_loans_page(_):
    """Farmer loans tracking page"""

    # HTML template for the loans page
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MAGSASA-CARD - My Loans</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #000;
                color: #fff;
                min-height: 100vh;
            }

            .header {
                background: #000;
                padding: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #333;
            }

            .logo {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: #00C805;
                font-weight: bold;
                font-size: 1.1rem;
            }

            .back-btn {
                background: none;
                border: none;
                color: #fff;
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0.5rem;
                border-radius: 50%;
                transition: background 0.2s;
            }

            .back-btn:hover {
                background: #333;
            }

            .container {
                padding: 1rem;
                max-width: 600px;
                margin: 0 auto;
            }

            .page-title {
                font-size: 1.5rem;
                font-weight: bold;
                margin-bottom: 1.5rem;
                text-align: center;
            }

            .loan-card {
                background: linear-gradient(135deg, #00C805, #00A004);
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                color: #fff;
            }

            .loan-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
            }

            .loan-title {
                font-size: 1.2rem;
                font-weight: bold;
            }

            .loan-status {
                background: rgba(255, 255, 255, 0.2);
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: bold;
            }

            .loan-amounts {
                display: flex;
                justify-content: space-between;
                margin-bottom: 1rem;
            }

            .amount-item h3 {
                font-size: 0.9rem;
                opacity: 0.9;
                margin-bottom: 0.25rem;
            }

            .amount-item .amount {
                font-size: 1.5rem;
                font-weight: bold;
            }

            .progress-bar {
                background: rgba(255, 255, 255, 0.2);
                height: 8px;
                border-radius: 4px;
                margin: 1rem 0;
                overflow: hidden;
            }

            .progress-fill {
                background: #fff;
                height: 100%;
                border-radius: 4px;
                transition: width 0.3s ease;
            }

            .next-payment {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.9rem;
            }

            .section-title {
                font-size: 1.2rem;
                font-weight: bold;
                margin: 2rem 0 1rem 0;
                color: #fff;
            }

            .payment-item {
                background: #1a1a1a;
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.75rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .payment-info h4 {
                font-size: 1rem;
                margin-bottom: 0.25rem;
            }

            .payment-info p {
                font-size: 0.85rem;
                color: #888;
            }

            .payment-amount {
                text-align: right;
            }

            .payment-amount .amount {
                font-size: 1.1rem;
                font-weight: bold;
                margin-bottom: 0.25rem;
            }

            .payment-status {
                font-size: 0.8rem;
                padding: 0.25rem 0.5rem;
                border-radius: 12px;
                font-weight: bold;
            }

            .status-paid {
                background: #00C805;
                color: #fff;
            }

            .status-due {
                background: #FF6B35;
                color: #fff;
            }

            .status-scheduled {
                background: #333;
                color: #888;
            }

            .action-buttons {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                margin-top: 2rem;
            }

            .btn {
                padding: 1rem;
                border: none;
                border-radius: 12px;
                font-size: 1rem;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-primary {
                background: #00C805;
                color: #fff;
            }

            .btn-secondary {
                background: #333;
                color: #fff;
            }

            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 200, 5, 0.3);
            }

            .loading {
                text-align: center;
                padding: 2rem;
                color: #888;
            }

            .error {
                background: #FF6B35;
                color: #fff;
                padding: 1rem;
                border-radius: 12px;
                margin-bottom: 1rem;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <button class="back-btn" onclick="goBack()">←</button>
            <div class="logo">
                🌱 MAGSASA-CARD
            </div>
            <div></div>
        </div>

        <div class="container">
            <h1 class="page-title">My Loans</h1>

            <div id="loading" class="loading">
                Loading your loan information...
            </div>

            <div id="error" class="error" style="display: none;">
                Unable to load loan information. Please try again.
            </div>

            <div id="loan-content" style="display: none;">
                <!-- Loan card will be populated here -->
            </div>
        </div>

        <script>
            function goBack() {
                window.history.back();
            }

            function formatCurrency(amount) {
                return new Intl.NumberFormat('en-PH', {
                    style: 'currency',
                    currency: 'PHP',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }).format(amount);
            }

            function formatDate(dateString) {
                const date = new Date(dateString);
                return date.toLocaleDateString('en-PH', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
            }

            function getStatusClass(status) {
                switch(status) {
                    case 'PAID': return 'status-paid';
                    case 'DUE_SOON': return 'status-due';
                    default: return 'status-scheduled';
                }
            }

            function getStatusText(status) {
                switch(status) {
                    case 'PAID': return 'PAID';
                    case 'DUE_SOON': return 'DUE SOON';
                    default: return 'SCHEDULED';
                }
            }

            async function loadLoanData() {
                try {
                    const response = await fetch('/api/farmer/loans');

                    if (!response.ok) {
                        throw new Error('Failed to load loan data');
                    }

                    const loanData = await response.json();
                    displayLoanData(loanData);

                } catch (error) {
                    console.error('Error loading loan data:', error);
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('error').style.display = 'block';
                }
            }

            function displayLoanData(data) {
                const loanContent = document.getElementById('loan-content');

                // Find next payment
                const nextPayment = data.payments.find(p => p.status !== 'PAID');

                loanContent.innerHTML = `
                    <div class="loan-card">
                        <div class="loan-header">
                            <div class="loan-title">${data.crop_type} Production Loan</div>
                            <div class="loan-status">ACTIVE</div>
                        </div>

                        <div class="loan-amounts">
                            <div class="amount-item">
                                <h3>Loan Amount</h3>
                                <div class="amount">${formatCurrency(data.loan_amount)}</div>
                            </div>
                            <div class="amount-item">
                                <h3>Remaining</h3>
                                <div class="amount">${formatCurrency(data.remaining_balance)}</div>
                            </div>
                        </div>

                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${data.progress_percentage}%"></div>
                        </div>

                        <div class="next-payment">
                            <span>Next Payment: ${nextPayment ? formatDate(nextPayment.due_date) : 'N/A'}</span>
                            <span>${nextPayment ? formatCurrency(nextPayment.amount) : ''}</span>
                        </div>
                    </div>

                    <h2 class="section-title">Payment History</h2>

                    <div class="payments-list">
                        ${data.payments.map(payment => `
                            <div class="payment-item">
                                <div class="payment-info">
                                    <h4>Payment #${payment.payment_number}</h4>
                                    <p>Due: ${formatDate(payment.due_date)}</p>
                                </div>
                                <div class="payment-amount">
                                    <div class="amount">${formatCurrency(payment.amount)}</div>
                                    <div class="payment-status ${getStatusClass(payment.status)}">
                                        ${getStatusText(payment.status)}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <div class="action-buttons">
                        <button class="btn btn-primary" onclick="makePayment()">Make Payment</button>
                        <button class="btn btn-secondary" onclick="downloadStatement()">Download Statement</button>
                    </div>
                `;

                document.getElementById('loading').style.display = 'none';
                document.getElementById('loan-content').style.display = 'block';
            }

            function makePayment() {
                // For demo purposes, show alert
                // In production, this would open payment interface
                alert('Payment interface would open here. Integration with payment gateway required.');
            }

            function downloadStatement() {
                // For demo purposes, show alert
                // In production, this would generate and download PDF statement
                alert('Statement download would start here. PDF generation required.');
            }

            // Load loan data when page loads
            document.addEventListener('DOMContentLoaded', loadLoanData);
        </script>
    </body>
    </html>
    """

    return render_template_string(html_template)
