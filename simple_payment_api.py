
from flask import Flask, jsonify
import sqlite3
import os

app = Flask(__name__)

@app.route('/api/test/farmer/loans')
def test_farmer_loans():
    """Test endpoint for farmer loans"""
    try:
        db_path = os.path.join('agsense.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get farmer data
        cursor.execute("""
            SELECT id, full_name, crop_type, loan_amount, loan_status, agscore
            FROM farmers WHERE id = 1
        """)
        farmer = cursor.fetchone()
        
        if not farmer:
            return jsonify({'error': 'Farmer not found'}), 404
        
        # Get payments
        cursor.execute("""
            SELECT payment_number, amount, due_date, status
            FROM payments WHERE farmer_id = 1
            ORDER BY payment_number
        """)
        payments = cursor.fetchall()
        
        # Calculate totals
        loan_amount = farmer[3]
        monthly_payment = loan_amount / 12
        paid_count = len([p for p in payments if p[3] == 'PAID'])
        total_paid = monthly_payment * paid_count
        remaining = loan_amount - total_paid
        progress = (total_paid / loan_amount * 100) if loan_amount > 0 else 0
        
        response = {
            'farmer_id': farmer[0],
            'full_name': farmer[1],
            'crop_type': farmer[2],
            'loan_amount': farmer[3],
            'loan_status': farmer[4],
            'agscore': farmer[5],
            'total_paid': total_paid,
            'remaining_balance': remaining,
            'progress_percentage': progress,
            'payments': [
                {
                    'payment_number': p[0],
                    'amount': p[1],
                    'due_date': p[2],
                    'status': p[3]
                } for p in payments
            ]
        }
        
        conn.close()
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
