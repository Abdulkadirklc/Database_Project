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
            sql_check = "SELECT 1 FROM `Group` WHERE group_id = %s"
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
    Query Parameters: group_id (int)
    """
    group_id = request.args.get('group_id', type=int)

    if not group_id:
        return jsonify({"error": "Group ID is required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch members and their roles
            sql = """
            SELECT u.username, m.user_role 
            FROM Membership m
            JOIN `User` u ON m.user_id = u.user_id
            WHERE m.group_id = %s
            """
            cursor.execute(sql, (group_id,))
            members = cursor.fetchall()

            # Check if the group has any members
            if not members:
                return jsonify({"error": "Group not found"}), 404  # If no members found
    finally:
        conn.close()

    return jsonify(members), 200

@membership_bp.route('/user/groups', methods=['GET'])
def list_user_groups():
    """
    GET /membership/user/groups - List all groups a user is a member of with their roles.
    Query Parameters: username (str)
    """
    username = request.args.get('username')  # Get username from query parameters

    if not username:
        return jsonify({"error": "Username is required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Get user_id from username
            sql_get_user_id = "SELECT user_id FROM `User` WHERE username = %s"
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

            # If no groups found, return appropriate message
            if not groups:
                return jsonify({"error": "User is not a member of any group"}), 404
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
            JOIN `User` u ON m.user_id = u.user_id
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
    Expects JSON: { "group_id": int, "user_id": int, "role": str }
    """
    data = request.get_json() or {}
    group_id = data.get('group_id')
    user_id_to_update = data.get('user_id')  # User whose role we want to update
    new_role = data.get('role')

    if not group_id or not user_id_to_update or not new_role:
        return jsonify({"error": "Group ID, User ID, and Role are required"}), 400

    # Ensure the role is valid
    if new_role not in ['Member', 'Guest', 'Admin']:
        return jsonify({"error": "Invalid role. Only 'Member', 'Guest' and 'Admin' are allowed."}), 400

    current_user_id = g.current_user_id  # Current user ID from JWT

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the current user is a member of the given group
            sql_check_membership = """
            SELECT user_role
            FROM Membership
            WHERE user_id = %s AND group_id = %s
            """
            cursor.execute(sql_check_membership, (current_user_id, group_id))
            current_user_membership = cursor.fetchone()

            if not current_user_membership:
                return jsonify({"error": "You are not a member of this group"}), 403

            current_user_role = current_user_membership['user_role']

            # Admin can update any user's role in their group
            if current_user_role == 'Admin':
                if user_id_to_update == current_user_id:
                    # Admin can resign from being Admin (become Member)
                    if new_role == 'Admin':
                        return jsonify({"error": "You are already an Admin."}), 403
                    # Admin can choose to become a Member
                    sql_check_admin_count = """
                    SELECT COUNT(*) as admin_count
                    FROM Membership
                    WHERE group_id = %s AND user_role = 'Admin'
                    """
                    cursor.execute(sql_check_admin_count, (group_id,))
                    admin_count = cursor.fetchone()['admin_count']
                    if admin_count <= 1 and new_role == 'Member':
                        return jsonify({"error": "Cannot remove the last admin of the group."}), 400

                # If changing to Admin, ensure there are at most 2 admins
                if new_role == 'Admin':
                    sql_check_admin_count = """
                    SELECT COUNT(*) as admin_count
                    FROM Membership
                    WHERE group_id = %s AND user_role = 'Admin'
                    """
                    cursor.execute(sql_check_admin_count, (group_id,))
                    admin_count = cursor.fetchone()['admin_count']
                    if admin_count >= 2:
                        return jsonify({"error": "Cannot add more than 2 admins to the group"}), 400

                # Perform the role update (whether it is an admin promotion or resignation)
                sql_update_role = """
                UPDATE Membership
                SET user_role = %s
                WHERE user_id = %s AND group_id = %s
                """
                cursor.execute(sql_update_role, (new_role, user_id_to_update, group_id))
                conn.commit()
                return jsonify({"message": "User role updated successfully."}), 200

            # Non-admin user can update only their own role
            elif current_user_id == user_id_to_update:
                # Prevent non-admin users from making themselves admin
                if new_role == 'Admin':
                    return jsonify({"error": "You cannot assign yourself the Admin role"}), 403

                sql_update_self_role = """
                UPDATE Membership
                SET user_role = %s
                WHERE user_id = %s AND group_id = %s
                """
                cursor.execute(sql_update_self_role, (new_role, current_user_id, group_id))
                conn.commit()
                return jsonify({"message": "Your role has been updated successfully."}), 200

            else:
                return jsonify({"error": "Unauthorized action"}), 403
    finally:
        conn.close()



@membership_bp.route('/remove', methods=['DELETE'])
@jwt_required  # Requires valid JWT
def remove_user_from_group():
    """
    DELETE /membership/remove - Remove a user from a group.
    Only admin or the user themselves can remove a user.
    Ensures there is always at least one admin in the group.
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
            # Check if the user is a member of the group
            cursor.execute("SELECT user_role FROM Membership WHERE group_id = %s AND user_id = %s", (group_id, user_id))
            membership = cursor.fetchone()

            if not membership:
                return jsonify({"error": "User not a member of the group"}), 404

            user_role = membership[0]
            is_admin = user_role == 'Admin'

            # Admin can remove any member, user can only remove themselves
            if not is_admin and current_user_id != user_id:
                return jsonify({"error": "Unauthorized. Only admins or the user themselves can remove members."}), 403

            # If admin, check that they're removing from their own group and there's still at least one admin left
            if is_admin:
                cursor.execute("SELECT COUNT(*) FROM Membership WHERE group_id = %s AND user_role = 'Admin'", (group_id,))
                admin_count = cursor.fetchone()[0]

                if admin_count <= 1 and current_user_id == user_id:
                    return jsonify({"error": "There must be at least one admin in the group."}), 400

            # Remove the user from the group
            cursor.execute("DELETE FROM Membership WHERE group_id = %s AND user_id = %s", (group_id, user_id))
            conn.commit()

    except Exception as e:
        conn.rollback()  # Rollback in case of error
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify({"message": "User removed from the group successfully."}), 200


