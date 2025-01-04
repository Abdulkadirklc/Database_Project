from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

membership_bp = Blueprint('membership_bp', __name__)

@membership_bp.route('/', methods=['POST'])  
@jwt_required
def add_user_to_group():
    """
    POST /membership/ - Add a user to a group.
    Expects JSON: { "group_id": int, "role": str }
    """
    data = request.get_json() or {}
    group_id = data.get('group_id')
    role = data.get('role', 'Member')

    # Ensure group_id is provided
    if not group_id:
        return jsonify({"error": "Group ID is required"}), 400

    # Ensure the role is valid
    if role not in ['Member', 'Admin', 'Guest']:
        return jsonify({"error": "Invalid role"}), 400

    user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if group exists
            sql_check = "SELECT 1 FROM Group WHERE group_id = %s"
            cursor.execute(sql_check, (group_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Group not found"}), 404

            # Check if user is already a member
            sql_check_membership = "SELECT 1 FROM Membership WHERE user_id = %s AND group_id = %s"
            cursor.execute(sql_check_membership, (user_id, group_id))
            if cursor.fetchone():
                return jsonify({"error": "User already a member of this group"}), 400

            # Add user to the group
            sql_insert = """
            INSERT INTO Membership (user_id, group_id, user_role)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql_insert, (user_id, group_id, role))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "User added to the group successfully."}), 201

@membership_bp.route('/', methods=['GET'])
def list_group_members():
    """
    GET /membership/ - List all members of a group with their roles.
    Expects JSON: { "group_id": int }
    """
    data = request.get_json() or {}
    group_id = data.get('group_id')

    if not group_id:
        return jsonify({"error": "Group ID is required"}), 400

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

@membership_bp.route('/user/groups', methods=['GET'])
def list_user_groups():
    """
    GET /membership/user/groups - List all groups a user is a member of with their roles.
    Expects JSON: { "username": str }
    """
    data = request.get_json() or {}
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

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

@membership_bp.route('/role', methods=['PUT'])
@jwt_required  # Requires valid JWT
def update_user_role():
    """
    PUT /membership/role - Update a user's role in their group.
    Expects JSON: { "user_id", "role" }
    """
    data = request.get_json() or {}
    user_id_to_update = data.get('user_id')  # User whose role we want to update
    new_role = data.get('role')

    # Ensure the role is valid
    if new_role not in ['Member', 'Admin', 'Guest']:
        return jsonify({"error": "Invalid role"}), 400

    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the current user is an admin of the group the target user belongs to
            sql_check_admin = """
            SELECT m.group_id
            FROM Membership m
            WHERE m.user_id = %s AND m.user_role = 'Admin'
            """
            cursor.execute(sql_check_admin, (current_user_id,))
            admin_groups = cursor.fetchall()

            # If user is not an admin in any group, deny the request
            if not admin_groups:
                return jsonify({"error": "Unauthorized. Only admins can change roles."}), 403

            # Check if the user to update is a member of any group
            sql_check_member = """
            SELECT user_role, group_id FROM Membership WHERE user_id = %s
            """
            cursor.execute(sql_check_member, (user_id_to_update,))
            current_role_data = cursor.fetchone()

            if not current_role_data:
                return jsonify({"error": "User not a member of any group"}), 404

            current_role = current_role_data['user_role']
            group_id = current_role_data['group_id']

            # If changing from Admin to another role, ensure there is at least 1 admin in the group
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

            # Update the user's role
            sql_update_role = "UPDATE Membership SET user_role = %s WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_update_role, (new_role, group_id, user_id_to_update))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "User role updated successfully."}), 200



@membership_bp.route('/remove', methods=['DELETE'])
@jwt_required  # Requires valid JWT
def remove_user_from_group():
    """
    DELETE /membership/remove - Remove a user from a group.
    Only admin or the user themselves can remove a user.
    Admin can only remove members from their own group.
    Expects JSON: { "group_id": <group_id>, "user_id": <user_id> }
    """
    data = request.get_json() or {}
    group_id = data.get('group_id')
    user_id = data.get('user_id')

    if not group_id or not user_id:
        return jsonify({"error": "group_id and user_id are required"}), 400

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

            # Check if the current user is trying to remove their own membership
            if current_user_id == user_id:
                is_admin = True  # Allow user to remove themselves regardless of admin status

            # Check if the user is a member of the group
            sql_check_member = "SELECT 1 FROM Membership WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_check_member, (group_id, user_id))
            is_member = cursor.fetchone()

            if not is_member:
                return jsonify({"error": "User not a member of the group"}), 404

            # Check if the user is not authorized to remove others (only admins can remove others)
            if not is_admin and current_user_id != user_id:
                return jsonify({"error": "Unauthorized. Only admins or the user themselves can remove members."}), 403

            # If user is admin, ensure they are trying to remove from their own group
            if is_admin:
                sql_check_group_owner = "SELECT 1 FROM Membership WHERE group_id = %s AND user_id = %s"
                cursor.execute(sql_check_group_owner, (group_id, current_user_id))
                if not cursor.fetchone():
                    return jsonify({"error": "Admin can only remove users from their own group."}), 403

            # Delete the membership
            sql_delete = "DELETE FROM Membership WHERE group_id = %s AND user_id = %s"
            cursor.execute(sql_delete, (group_id, user_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "User removed from the group successfully."}), 200

