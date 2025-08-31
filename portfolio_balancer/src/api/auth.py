from flask import jsonify, request
from supabase import Client
import os

# Supabase client will be initialized in app.py and passed here
supabase: Client = None

def init_auth_routes(app, sb_client):
    global supabase
    supabase = sb_client

    @app.route('/auth/signup', methods=['POST'])
    def signup():
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'error': 'Missing username, email, or password'}), 400

        try:
            # Supabase auth.sign_up_with_password handles user creation and authentication
            response = supabase.auth.sign_up_with_password({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "username": username
                    }
                }
            })
            
            # Check if user creation was successful
            if response.user:
                # Optionally, insert user details into a 'users' table if you need more custom fields
                # beyond what Supabase Auth stores by default.
                # For this task, we'll assume the user_id from auth.sign_up_with_password is sufficient.
                user_id = response.user.id
                return jsonify({"message": "Account created", "user_id": user_id}), 201
            else:
                # Handle cases where sign_up_with_password might not return a user but no explicit error
                return jsonify({'error': 'Failed to create account: No user returned'}), 500

        except Exception as e:
            # Supabase client exceptions might contain more specific error details
            # For example, if email already exists, Supabase will return an error.
            return jsonify({'error': str(e)}), 500

    @app.route('/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({'error': 'Missing email or password'}), 400

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.session and response.session.access_token:
                return jsonify({"token": response.session.access_token}), 200
            else:
                return jsonify({'error': 'Invalid credentials or failed to log in'}), 401

        except Exception as e:
            return jsonify({'error': str(e)}), 401 # Use 401 for authentication failures