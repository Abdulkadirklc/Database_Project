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
