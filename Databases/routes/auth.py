import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, g

JWT_SECRET_KEY = "THIS-IS-A-SUPER-SECRET-KEY"  
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 3600  # 1 hour

def generate_jwt_token(user_id):
    """
    Generate a JWT token containing user_id in its payload.
    The token expires in JWT_EXP_DELTA_SECONDS.
    """
    now = datetime.now(timezone.utc)
    payload = {
        'user_id': user_id,
        'exp': now + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
        'iat': now
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    # jwt.encode() returns a str in some modes, bytes in others.
    # We'll ensure it's str for consistent usage.
    return token if isinstance(token, str) else token.decode('utf-8')

def jwt_required(func):
    """
    Decorator that checks for a valid JWT in the Authorization header.
    If valid, sets g.current_user_id and calls the route handler.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        # Expecting header like: Authorization: Bearer <token>
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format. Expected 'Bearer <token>'"}), 401

        token = parts[1]
        try:
            decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = decoded.get("user_id")
            # Save the user_id to flask.g so the route can access it
            g.current_user_id = user_id
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return func(*args, **kwargs)

    return wrapper
