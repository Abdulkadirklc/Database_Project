from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from routes import get_connection
from routes.auth import generate_jwt_token, jwt_required

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/', methods=['GET'])
def get_users():
    """
    GET /users - Return paginated username, email, bio from users.
    Supports advanced search by 'query' parameter (case-insensitive) for username or email.
    Query Parameters:
        - query: String to search for users whose username or email starts with the query string.
        - page: Page number for pagination (default: 1).
        - size: Number of results per page (default: 20, max: 100).
    """
    # Get query parameters
    search_query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    # Ensure size is within a reasonable limit
    if size > 100:
        size = 100

    # Calculate the offset for pagination
    offset = (page - 1) * size

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Prepare SQL for case-insensitive startswith search with pagination
            sql = """
            SELECT username, email, bio 
            FROM User
            WHERE (username LIKE %s OR email LIKE %s)
            LIMIT %s OFFSET %s
            """
            # Adjust the query for startswith by adding the `%` only after the search query
            cursor.execute(sql, (f"{search_query}%", f"{search_query}%", size, offset))
            rows = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(rows), 200


@user_bp.route('/', methods=['POST'])
def create_user():
    """
    POST /users - Create a new user (register).
    Expects JSON: { "username", "email", "password", "bio"(optional) }
    """
    data = request.get_json() or {}
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Hash the password before storing
    hashed_password = generate_password_hash(data['password'])

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO User (username, email, password, bio)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['username'],
                data['email'],
                hashed_password,
                data.get('bio', '')
            ))
            conn.commit()
            new_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({"message": "User created successfully", "user_id": new_id}), 201

@user_bp.route('/login', methods=['POST'])
def login_user():
    """
    POST /users/login - User login, returns JWT if credentials are valid.
    Expects JSON: { "username", "password" }
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT user_id, password FROM User WHERE username=%s"
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "Username does not exists."}), 401

    stored_hashed_pwd = row['password']
    if not check_password_hash(stored_hashed_pwd, password):
        return jsonify({"error": "Invalid password"}), 401

    # Generate JWT
    token = generate_jwt_token(row['user_id'])
    return jsonify({"message": "Login successful", "token": token}), 200

@user_bp.route('/<string:username>', methods=['GET'])
def get_user(username):
    """
    GET /users/<username> - Retrieve a single user by username.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT username, email, bio FROM User WHERE username = %s"
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return jsonify(row), 200


@user_bp.route('/<string:username>', methods=['PUT'])
@jwt_required  # Requires valid JWT
def update_user(username):
    """
    PUT /users/<username> - Update an existing user (but cannot change username).
    Only the user can update their own account information.
    """
    # Extract user_id from JWT
    current_user_id = g.current_user_id  

    data = request.get_json() or {}

    # If a new password is provided, hash it
    updated_password = data.get('password')
    if updated_password:
        updated_password = generate_password_hash(updated_password)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch user_id based on the provided username
            sql_check = "SELECT user_id FROM User WHERE username=%s"
            cursor.execute(sql_check, (username,))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "User not found"}), 404

            user_id = result['user_id']

            # Ensure the current user matches the user being updated
            if current_user_id != user_id:
                return jsonify({"error": "Unauthorized access. You can only update your own account."}), 403

            # Perform the update
            sql_update = """
            UPDATE User
            SET email=%s, password=%s, bio=%s
            WHERE user_id=%s
            """
            cursor.execute(sql_update, (
                data.get('email', ''), 
                updated_password or None,  # Use None if no new password
                data.get('bio', ''), 
                user_id
            ))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": f"User '{username}' updated successfully."}), 200


@user_bp.route('/<string:username>', methods=['DELETE'])
@jwt_required  # Requires valid JWT
def delete_user(username):
    """
    DELETE /users/<username> - Remove a user by username.
    Only the authenticated user can delete their own account.
    """
    # Get current user ID from the JWT
    current_user_id = g.current_user_id  

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Retrieve user_id from the provided username
            sql_check = "SELECT user_id FROM User WHERE username=%s"
            cursor.execute(sql_check, (username,))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "User not found"}), 404

            user_id = result['user_id']

            # Ensure the current user matches the user being deleted
            if current_user_id != user_id:
                return jsonify({"error": "Unauthorized access. You can only delete your own account."}), 403

            # Delete the user
            sql_delete = "DELETE FROM User WHERE user_id=%s"
            cursor.execute(sql_delete, (user_id,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": f"User '{username}' deleted successfully."}), 200

