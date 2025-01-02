from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

membership_bp = Blueprint('membership_bp', __name__)

@membership_bp.route('/<int:group_id>', methods=['POST'])
@jwt_required  # Requires valid JWT
def add_user_to_group(group_id):
    """
    POST /membership/<group_id> - Add a user to a group.
    Expects JSON: { "role" }
    """
    data = request.get_json() or {}
    role = data.get('role', 'Member')

    # Ensure the role is valid
    if role not in ['Member', 'Admin', 'Guest']:
        return jsonify({"error": "Invalid role"}), 400

    user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_check = "SELECT 1 FROM Group WHERE group_id = %s"
            cursor.execute(sql_check, (group_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Group not found"}), 404

            sql_check_membership = "SELECT 1 FROM Membership WHERE user_id = %s AND group_id = %s"
            cursor.execute(sql_check_membership, (user_id, group_id))
            if cursor.fetchone():
                return jsonify({"error": "User already a member of this group"}), 400

            sql_insert = """
            INSERT INTO Membership (user_id, group_id, user_role)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql_insert, (user_id, group_id, role))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "User added to the group successfully."}), 201

@membership_bp.route('/<int:group_id>', methods=['GET'])
@jwt_required  # Requires valid JWT
def list_group_members(group_id):
    """
    GET /membership/<group_id> - List all members of a group with their roles.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT u.username, m.user_role 
            FROM Membership m
            JOIN User u ON m.user_id = u.user_id
            WHERE m.group_id = %s
            """
            cursor.execute(sql, (group_id,))
            members = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(members), 200

@membership_bp.route('/<int:group_id>/<int:user_id>', methods=['DELETE'])
@jwt_required  # Requires valid JWT
def remove_user_from_group(group_id, user_id):
    """
    DELETE /membership/<group_id>/<user_id> - Remove a user from a group.
    Only admin can remove a user.
    """
    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the user is an admin of the group
            sql_check_admin = """
            SELECT 1 FROM Membership WHERE group_id = %s AND user_id = %s AND user_role = 'Admin'
            """
            cursor.execute(sql_check_admin, (group_id, current_user_id))
            if not cursor.fetchone():
                return jsonify({"error": "Unauthorized. Only admins can remove members."}), 403

            # Check if the user is a member of the group
            sql_check_member = "SELECT 1 FROM Membership WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_check_member, (group_id, user_id))
            if not cursor.fetchone():
                return jsonify({"error": "User not a member of the group"}), 404

            # Delete the membership
            sql_delete = "DELETE FROM Membership WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_delete, (group_id, user_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "User removed from the group successfully."}), 200
