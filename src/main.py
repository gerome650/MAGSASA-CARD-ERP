import os
import sys
import time
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, redirect, session
from flask_cors import CORS
from src.database import db
from src.models.farmer import Farmer
from src.models.category import Category
from src.models.supplier import Supplier
from src.models.product import Product
from src.models.partner import Partner
from src.models.order import Order, OrderItem
from src.routes.user import user_bp
from src.routes.farmer import farmer_bp
from src.routes.product import product_bp
from src.routes.order import order_bp
from src.routes.partner import partner_bp
from src.routes.dashboard import dashboard_bp
from src.routes.analytics import analytics_bp
from src.routes.reports import reports_bp
from src.routes.category import category_bp
from src.routes.supplier import supplier_bp
from src.routes.farmer_orders import farmer_orders_bp
from src.routes.partnership import partnership_bp
from src.routes.financial import financial_bp
from src.routes.auth import auth_bp
from src.routes.image_upload import image_bp
from src.routes.farmer_loans import farmer_loans_bp
from src.routes.kaani_enhanced import kaani_enhanced_bp
from src.routes.prequalification import prequalification_bp
from src.simple_auth import simple_auth_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Session configuration for better security
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(farmer_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(order_bp, url_prefix='/api')
app.register_blueprint(partner_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp)  # No prefix for dashboard routes
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api')
app.register_blueprint(category_bp, url_prefix='/api')
app.register_blueprint(supplier_bp, url_prefix='/api')
app.register_blueprint(farmer_orders_bp, url_prefix='/api')
app.register_blueprint(partnership_bp, url_prefix='/api')
app.register_blueprint(financial_bp, url_prefix='/api')
# app.register_blueprint(auth_bp)  # Disabled - using simple auth instead
app.register_blueprint(simple_auth_bp)  # Simple authentication
app.register_blueprint(image_bp)
app.register_blueprint(farmer_loans_bp)
app.register_blueprint(kaani_enhanced_bp)  # Enhanced KaAni Assistant integration
app.register_blueprint(prequalification_bp)  # Pre-qualification assessment API

# Add root route handler
@app.route('/')
def index():
    """Root route - redirect to appropriate dashboard based on login status"""
    if 'user_id' in session:
        return redirect('/dashboard')
    else:
        return redirect('/login.html')

# Role-specific dashboard routes
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/manager')
def manager_dashboard():
    """Manager dashboard"""
    return send_from_directory(app.static_folder, 'manager_dashboard.html')

@app.route('/officer')
def officer_dashboard():
    """Officer dashboard"""
    return send_from_directory(app.static_folder, 'enhanced_officer_dashboard.html')

@app.route('/farmer')
def farmer_dashboard():
    """Farmer dashboard"""
    return send_from_directory(app.static_folder, 'farmer_dashboard.html')

@app.route('/farmer/loans/demo')
def farmer_loans_demo():
    """Demo page for farmer loan tracking features"""
    return send_from_directory(app.static_folder, 'farmer_loans_demo.html')

@app.route('/officer/enhanced')
def enhanced_officer_dashboard():
    """Enhanced field officer dashboard with offline capabilities"""
    return send_from_directory(app.static_folder, 'enhanced_officer_dashboard.html')

@app.route('/officer/offline-demo')
def offline_sync_demo():
    """Offline synchronization demo for field officers"""
    return send_from_directory(app.static_folder, 'offline_sync_demo.html')

# Simple test endpoint
@app.route('/api/test')
def test_endpoint():
    """Simple test endpoint"""
    return {'message': 'test works'}, 200

# Health check endpoint for monitoring and chaos testing
@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring and chaos testing"""
    try:
        # Basic health check - verify database connection
        db_status = 'unknown'
        try:
            with app.app_context():
                # Use text() for SQLAlchemy 2.0 compatibility
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                db_status = 'connected'
        except Exception as db_error:
            db_status = f'error: {str(db_error)}'
        
        return {
            'status': 'healthy',
            'timestamp': time.time(),
            'service': 'MAGSASA-CARD-ERP',
            'version': '1.0.0',
            'database': db_status
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': time.time(),
            'service': 'MAGSASA-CARD-ERP',
            'error': str(e)
        }, 503

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'agsense.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Removed problematic catch-all route that was overriding specific dashboard routes


if __name__ == '__main__':
    # Security: Use environment variables for host and debug settings
    # Default to secure values: localhost binding and debug off
    flask_host = os.getenv('FLASK_HOST', '127.0.0.1')
    flask_debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    # Port configuration with environment variable support
    # Default to 8000 for consistency with chaos testing, fallback to 5001 for backward compatibility
    flask_port = int(os.getenv('APP_PORT', os.getenv('FLASK_PORT', '8000')))
    
    print(f"🚀 Starting Flask application on {flask_host}:{flask_port}")
    print(f"   Health endpoint: http://{flask_host}:{flask_port}/api/health")
    print(f"   Set APP_PORT environment variable to change port")
    
    # Note: For Docker/load testing, set FLASK_HOST=0.0.0.0 in environment
    # This avoids hardcoding bind-all-interfaces (Bandit B104)
    app.run(host=flask_host, port=flask_port, debug=flask_debug)  # nosec B104
