#!/usr/bin/env python3.11

from flask import Blueprint, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os

simple_auth_bp = Blueprint('simple_auth', __name__)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'agsense.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@simple_auth_bp.route('/api/auth/login', methods=['POST'])
def simple_login():
    """Simple login endpoint that works with our database"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Hash the provided password
        password_hash = hash_password(password)
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find user by username
        cursor.execute('''
            SELECT id, username, password_hash, first_name, last_name, email, role, is_active
            FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['first_name'] = user['first_name']
        session['last_name'] = user['last_name']
        
        # Determine redirect URL based on role
        redirect_urls = {
            'super_admin': '/admin',
            'manager': '/manager',
            'officer': '/officer',
            'farmer': '/farmer'
        }
        
        redirect_url = redirect_urls.get(user['role'], '/admin')
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'email': user['email'],
                'role': user['role']
            },
            'redirect_url': redirect_url
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@simple_auth_bp.route('/api/auth/logout', methods=['POST'])
def simple_logout():
    """Enhanced logout endpoint with proper session management"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'message': 'Already logged out'}), 200
        
        # Log the logout action for security auditing
        user_id = session.get('user_id')
        username = session.get('username')
        print(f"User logout: {username} (ID: {user_id})")
        
        # Clear all session data
        session.clear()
        
        # Force session to be saved/cleared immediately
        session.permanent = False
        
        return jsonify({
            'message': 'Logout successful',
            'redirect_url': '/login.html'
        }), 200
        
    except Exception as e:
        print(f"Logout error: {e}")
        # Even if there's an error, clear the session for security
        session.clear()
        return jsonify({
            'message': 'Logout completed',
            'redirect_url': '/login.html'
        }), 200

@simple_auth_bp.route('/api/auth/logout', methods=['GET'])
def simple_logout_get():
    """Handle GET requests to logout (for direct URL access)"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return redirect('/login.html')
        
        # Log the logout action
        user_id = session.get('user_id')
        username = session.get('username')
        print(f"User logout via GET: {username} (ID: {user_id})")
        
        # Clear session
        session.clear()
        session.permanent = False
        
        # Redirect to login page
        return redirect('/login.html')
        
    except Exception as e:
        print(f"Logout GET error: {e}")
        session.clear()
        return redirect('/login.html')

@simple_auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, first_name, last_name, email, role, is_active
            FROM users 
            WHERE id = ? AND is_active = 1
        ''', (session['user_id'],))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            session.clear()
            return jsonify({'error': 'User not found'}), 401
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Failed to get user'}), 500
