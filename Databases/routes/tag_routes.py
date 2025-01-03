from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

tag_bp = Blueprint('tag_bp', __name__)

@tag_bp.route('/', methods=['POST'])
@jwt_required
def create_tag():
    """
    POST /tags - Create a new tag.
    Expects JSON: { "tag_name": "Tag name" }
    """
    data = request.get_json() or {}
    tag_name = data.get('tag_name')

    if not tag_name:
        return jsonify({"error": "Tag name is required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO Tag (tag_name)
            VALUES (%s)
            """
            cursor.execute(sql, (tag_name,))
            conn.commit()
            tag_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({"message": "Tag created successfully", "tag_id": tag_id}), 201


@tag_bp.route('/<int:tag_id>', methods=['PUT'])
@jwt_required
def update_tag(tag_id):
    """
    PUT /tags/<tag_id> - Update an existing tag by its ID.
    Expects JSON: { "tag_name": "Updated tag name" }
    """
    data = request.get_json() or {}
    new_tag_name = data.get('tag_name')

    if not new_tag_name:
        return jsonify({"error": "Tag name is required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Update the tag
            sql = """
            UPDATE Tag
            SET tag_name = %s
            WHERE tag_id = %s
            """
            cursor.execute(sql, (new_tag_name, tag_id))
            conn.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "Tag not found"}), 404
    finally:
        conn.close()

    return jsonify({"message": "Tag updated successfully"}), 200


@tag_bp.route('/<int:tag_id>', methods=['DELETE'])
@jwt_required
def delete_tag(tag_id):
    """
    DELETE /tags/<tag_id> - Delete a tag by its ID.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM Tag WHERE tag_id = %s"
            cursor.execute(sql, (tag_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "Tag not found"}), 404
    finally:
        conn.close()

    return jsonify({"message": "Tag deleted successfully"}), 200


@tag_bp.route('/', methods=['GET'])
def list_tags():
    """
    GET /tags - List all tags with optional search by name.
    Query Parameters:
        - query: String to search for in tag names.
    """
    search_query = request.args.get('query', '')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Search for tags by name (case-insensitive)
            sql = """
            SELECT tag_id, tag_name
            FROM Tag
            WHERE tag_name LIKE %s
            ORDER BY tag_name ASC
            """
            cursor.execute(sql, (f"%{search_query}%",))
            rows = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(rows), 200
