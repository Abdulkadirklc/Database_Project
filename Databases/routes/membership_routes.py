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

@membership_bp.route('/user/<username>/groups', methods=['GET'])
def list_user_groups(username):
    """
    GET /membership/user/<username>/groups - List all groups a user is a member of with their roles.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Get user_id from username
            sql_get_user_id = "SELECT user_id FROM User WHERE username = %s"
            cursor.execute(sql_get_user_id, (username,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not found"}), 404
            user_id = user['user_id']

            # Get groups and roles
            sql = """
            SELECT g.group_name, m.user_role 
            FROM Membership m
            JOIN `Group` g ON m.group_id = g.group_id
            WHERE m.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            groups = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(groups), 200

@membership_bp.route('/admins', methods=['GET'])
def list_all_admins():
    """
    GET /membership/admins - List all admins with their group names.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT g.group_name, u.username, m.user_role 
            FROM Membership m
            JOIN User u ON m.user_id = u.user_id
            JOIN `Group` g ON m.group_id = g.group_id
            WHERE m.user_role = 'Admin'
            """
            cursor.execute(sql)
            admins = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(admins), 200

@membership_bp.route('/<int:group_id>/<int:user_id>/role', methods=['PUT'])
@jwt_required  # Requires valid JWT
def update_user_role(group_id, user_id):
    """
    PUT /membership/<group_id>/<user_id>/role - Update a user's role in a group.
    Expects JSON: { "role" }
    There must be at least 1 admin and at most 2 admins in a group at all times.
    """
    data = request.get_json() or {}
    new_role = data.get('role')

    # Ensure the role is valid
    if new_role not in ['Member', 'Admin', 'Guest']:
        return jsonify({"error": "Invalid role"}), 400

    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the current user is an admin of the group
            sql_check_admin = """
            SELECT 1 FROM Membership WHERE group_id = %s AND user_id = %s AND user_role = 'Admin'
            """
            cursor.execute(sql_check_admin, (group_id, current_user_id))
            is_admin = cursor.fetchone()

            # Check if the user is a member of the group
            sql_check_member = "SELECT user_role FROM Membership WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_check_member, (group_id, user_id))
            current_role = cursor.fetchone()
            if not current_role:
                return jsonify({"error": "User not a member of the group"}), 404

            current_role = current_role['user_role']

            # If changing from Admin to another role, ensure there is at least 1 admin
            if current_role == 'Admin' and new_role != 'Admin':
                sql_check_admins = "SELECT COUNT(*) as admin_count FROM Membership WHERE group_id = %s AND user_role = 'Admin'"
                cursor.execute(sql_check_admins, (group_id,))
                admin_count = cursor.fetchone()['admin_count']
                if admin_count <= 1:
                    return jsonify({"error": "Cannot change role. There must be at least 1 admin in the group."}), 400

            # If changing to Admin, ensure there are at most 2 admins
            if new_role == 'Admin':
                sql_check_admins = "SELECT COUNT(*) as admin_count FROM Membership WHERE group_id = %s AND user_role = 'Admin'"
                cursor.execute(sql_check_admins, (group_id,))
                admin_count = cursor.fetchone()['admin_count']
                if admin_count >= 2:
                    return jsonify({"error": "Cannot change role. There can be at most 2 admins in the group."}), 400

            # Only admins can change roles, except for their own role
            if not is_admin and current_user_id != user_id:
                return jsonify({"error": "Unauthorized. Only admins can change roles."}), 403

            # Update the user's role
            sql_update_role = "UPDATE Membership SET user_role = %s WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_update_role, (new_role, group_id, user_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "User role updated successfully."}), 200


@membership_bp.route('/<int:group_id>/<int:user_id>', methods=['DELETE'])
@jwt_required  # Requires valid JWT
def remove_user_from_group(group_id, user_id):
    """
    DELETE /membership/<group_id>/<user_id> - Remove a user from a group.
    Only admin or the user themselves can remove a user.
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
            is_admin = cursor.fetchone()

            # Check if the user is a member of the group
            sql_check_member = "SELECT 1 FROM Membership WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_check_member, (group_id, user_id))
            is_member = cursor.fetchone()

            if not is_member:
                return jsonify({"error": "User not a member of the group"}), 404

            if not is_admin and current_user_id != user_id:
                return jsonify({"error": "Unauthorized. Only admins or the user themselves can remove members."}), 403

            # Delete the membership
            sql_delete = "DELETE FROM Membership WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_delete, (group_id, user_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "User removed from the group successfully."}), 200
