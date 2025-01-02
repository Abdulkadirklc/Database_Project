from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

group_bp = Blueprint('group_bp', __name__)

@group_bp.route('/', methods=['GET'])
def get_all_groups():
    """
    GET /groups - Return all groups with group_name and description.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT group_id, group_name, group_description FROM Group"
            cursor.execute(sql)
            rows = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(rows), 200

@group_bp.route('/', methods=['POST'])
@jwt_required  # Requires valid JWT
def create_group():
    """
    POST /groups - Create a new group.
    Expects JSON: { "group_name", "group_description", "created_by" }
    """
    data = request.get_json() or {}
    required_fields = ['group_name']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    group_name = data['group_name']
    group_description = data.get('group_description', '')
    # created_by = data.get('created_by')

    # Get the user ID from JWT
    created_by = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO Group (group_name, group_description, created_by)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (group_name, group_description, created_by))
            conn.commit()
            new_group_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({"message": "Group created successfully", "group_id": new_group_id}), 201

@group_bp.route('/<int:group_id>', methods=['GET'])
def get_group(group_id):
    """
    GET /groups/<group_id> - Retrieve a single group by ID.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT group_name, group_description FROM Group WHERE group_id = %s"
            cursor.execute(sql, (group_id,))
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "Group not found"}), 404

    return jsonify(row), 200

@group_bp.route('/<int:group_id>', methods=['PUT'])
@jwt_required  # Requires valid JWT
def update_group(group_id):
    """
    PUT /groups/<group_id> - Update an existing group's information.
    Only the creator (admin) can update the group.
    """
    # Get the current user ID from JWT
    current_user_id = g.current_user_id

    data = request.get_json() or {}
    group_name = data.get('group_name')
    group_description = data.get('group_description')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the group exists
            sql_check = "SELECT created_by FROM Group WHERE group_id = %s"
            cursor.execute(sql_check, (group_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "Group not found"}), 404

            creator_id = result['created_by']
            if current_user_id != creator_id:
                return jsonify({"error": "Unauthorized. Only the creator can update the group."}), 403

            # Perform the update
            sql_update = """
            UPDATE Group
            SET group_name = %s, group_description = %s
            WHERE group_id = %s
            """
            cursor.execute(sql_update, (group_name, group_description, group_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": f"Group '{group_id}' updated successfully."}), 200

@group_bp.route('/<int:group_id>', methods=['DELETE'])
@jwt_required  # Requires valid JWT
def delete_group(group_id):
    """
    DELETE /groups/<group_id> - Delete a group by ID.
    Only the creator (admin) can delete the group.
    """
    current_user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_check = "SELECT created_by FROM Group WHERE group_id = %s"
            cursor.execute(sql_check, (group_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "Group not found"}), 404

            creator_id = result['created_by']
            if current_user_id != creator_id:
                return jsonify({"error": "Unauthorized. Only the creator can delete the group."}), 403

            sql_delete = "DELETE FROM Group WHERE group_id = %s"
            cursor.execute(sql_delete, (group_id,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": f"Group '{group_id}' deleted successfully."}), 200
