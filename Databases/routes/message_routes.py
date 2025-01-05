from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

message_bp = Blueprint('message_bp', __name__)


@message_bp.route('/filter', methods=['GET'])
@jwt_required
def filter_messages_by_date():
    """
    GET /messages/filter - Filter messages by date range.
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD).
        - end_date: End date (YYYY-MM-DD).
        - group_id: Group ID to filter messages from a specific group.
        - page: Page number for pagination (default: 1).
        - size: Number of results per page (default: 20, max: 100).
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_id = request.args.get('group_id')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    if size > 100:
        size = 100

    offset = (page - 1) * size

    if not start_date or not end_date:
        return jsonify({"error": "Start date and end date are required"}), 400

    if not group_id:
        return jsonify({"error": "Group ID is required"}), 400

    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the user is a member of the group
            sql_check_membership = """
            SELECT COUNT(*) as is_member
            FROM Membership
            WHERE user_id = %s AND group_id = %s
            """
            cursor.execute(sql_check_membership, (current_user_id, group_id))
            membership_check = cursor.fetchone()

            if not membership_check['is_member']:
                return jsonify({"error": "You are not a member of this group"}), 403

            # Fetch messages within the date range
            sql = """
            SELECT message_id, user_message, message_time 
            FROM Message_Board
            WHERE group_id = %s AND message_time BETWEEN %s AND %s
            ORDER BY message_time DESC
            LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (group_id, start_date, end_date, size, offset))
            rows = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(rows), 200


@message_bp.route('/', methods=['GET'])
@jwt_required
def list_all_messages():
    """
    GET /messages - List all messages ordered from newest to oldest.
    Query Parameters:
        - group_id: Group ID to filter messages from a specific group.
        - page: Page number for pagination (default: 1).
        - size: Number of results per page (default: 20, max: 100).
    """
    group_id = request.args.get('group_id')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    if size > 100:
        size = 100

    offset = (page - 1) * size

    if not group_id:
        return jsonify({"error": "Group ID is required"}), 400

    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the user is a member of the group
            sql_check_membership = """
            SELECT COUNT(*) as is_member
            FROM Membership
            WHERE user_id = %s AND group_id = %s
            """
            cursor.execute(sql_check_membership, (current_user_id, group_id))
            membership_check = cursor.fetchone()

            if not membership_check['is_member']:
                return jsonify({"error": "You are not a member of this group"}), 403

            # Fetch all messages in the group ordered by newest to oldest
            sql = """
            SELECT message_id, group_id, user_id, user_message, message_time 
            FROM Message_Board
            WHERE group_id = %s
            ORDER BY message_time DESC
            LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (group_id, size, offset))
            rows = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(rows), 200

@message_bp.route('/', methods=['POST'])
@jwt_required
def create_message():
    """
    POST /messages - Create a new message.
    Expects JSON: { "user_message": "Message text", "group_id": Group ID }
    """
    data = request.get_json() or {}
    user_message = data.get('user_message')
    group_id = data.get('group_id')

    if not user_message:
        return jsonify({"error": "Message text is required"}), 400

    if not group_id:
        return jsonify({"error": "Group ID is required"}), 400

    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the user is a member of the group
            sql_check_membership = """
            SELECT COUNT(*) as is_member
            FROM Membership
            WHERE user_id = %s AND group_id = %s
            """
            cursor.execute(sql_check_membership, (current_user_id, group_id))
            membership_check = cursor.fetchone()

            if not membership_check['is_member']:
                return jsonify({"error": "You are not a member of this group"}), 403

            # Insert the message
            sql = """
            INSERT INTO Message_Board (user_id, group_id, user_message)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (current_user_id, group_id, user_message))
            conn.commit()
            message_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({"message": "Message created successfully", "message_id": message_id}), 201


@message_bp.route('/<int:message_id>', methods=['PUT'])
@jwt_required
def update_message(message_id):
    """
    PUT /messages/<message_id> - Update a message by its ID.
    Expects JSON: { "user_message": "Updated message text" }
    """
    data = request.get_json() or {}
    new_message = data.get('user_message')

    if not new_message:
        return jsonify({"error": "Updated message text is required"}), 400

    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the message exists and belongs to the user
            sql_check = """
            SELECT user_id
            FROM Message_Board
            WHERE message_id = %s
            """
            cursor.execute(sql_check, (message_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "Message not found"}), 404

            if result['user_id'] != current_user_id:
                return jsonify({"error": "Unauthorized access. You can only update your own messages."}), 403

            # Update the message
            sql_update = """
            UPDATE Message_Board
            SET user_message = %s
            WHERE message_id = %s
            """
            cursor.execute(sql_update, (new_message, message_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Message updated successfully"}), 200


@message_bp.route('/<int:message_id>', methods=['DELETE'])
@jwt_required
def delete_message(message_id):
    """
    DELETE /messages/<message_id> - Delete a message by its ID.
    Only the creator of the message or an admin of the group can delete it.
    """
    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the message exists and get its details
            sql_check_message = """
            SELECT user_id, group_id
            FROM Message_Board
            WHERE message_id = %s
            """
            cursor.execute(sql_check_message, (message_id,))
            message = cursor.fetchone()

            if not message:
                return jsonify({"error": "Message not found"}), 404

            message_creator_id = message['user_id']
            group_id = message['group_id']

            # Check if the current user is an admin of the group
            sql_check_admin = """
            SELECT COUNT(*) as is_admin
            FROM Membership
            WHERE user_id = %s AND group_id = %s AND user_role = 'Admin'
            """
            cursor.execute(sql_check_admin, (current_user_id, group_id))
            admin_check = cursor.fetchone()

            # Allow deletion if the user is the message creator or a group admin
            if current_user_id != message_creator_id and not admin_check['is_admin']:
                return jsonify({"error": "Unauthorized access. Only the creator or a group admin can delete this message."}), 403

            # Delete the message
            sql_delete = """
            DELETE FROM Message_Board
            WHERE message_id = %s
            """
            cursor.execute(sql_delete, (message_id,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Message deleted successfully"}), 200
