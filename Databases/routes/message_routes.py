from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

message_bp = Blueprint('message_bp', __name__)

@message_bp.route('/', methods=['POST'])
@jwt_required
def create_message():
    """
    POST /messages
    Protected by JWT. 
    Expects JSON: { "user_message": "Hello world" }
    """
    data = request.get_json() or {}
    user_message = data.get('user_message')
    if not user_message:
        return jsonify({"error": "Missing user_message"}), 400

    # g.user_id is set by @jwt_required if token is valid
    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO Message_Board (user_id, user_message)
            VALUES (%s, %s)
            """
            cursor.execute(sql, (current_user_id, user_message))
            conn.commit()
            new_msg_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({
        "message": "Message created successfully",
        "message_id": new_msg_id,
        "user_id": current_user_id
    }), 201
