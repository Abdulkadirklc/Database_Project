from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

event_tag_bp = Blueprint('event_tag_bp', __name__)

@event_tag_bp.route('/tags', methods=['POST'])
@jwt_required
def create_tags():
    """
    POST /events/tags - Add multiple tags to an event.
    Expects JSON: { "event_id": int, "tags": ["tag1", "tag2"] }
    """
    data = request.get_json() or {}
    event_id = data.get('event_id')
    tags = data.get('tags', [])

    if not event_id or not tags:
        return jsonify({"error": "Missing required fields."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for tag in tags:
                sql_tag = """
                INSERT INTO Tag (tag_name) VALUES (%s) ON DUPLICATE KEY UPDATE tag_id=LAST_INSERT_ID(tag_id)
                """
                cursor.execute(sql_tag, (tag,))
                tag_id = cursor.lastrowid

                sql_event_tag = """
                INSERT INTO Event_Tag (event_id, tag_id) VALUES (%s, %s)
                """
                cursor.execute(sql_event_tag, (event_id, tag_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Tags added successfully."}), 201


@event_tag_bp.route('/<int:event_id>/tags', methods=['GET'])
def get_event_tags(event_id):
    """
    GET /events/tags/<event_id> - Retrieve all tags for a specific event.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT t.tag_name FROM Tag t
            INNER JOIN Event_Tag et ON t.tag_id = et.tag_id
            WHERE et.event_id = %s
            """
            cursor.execute(sql, (event_id,))
            tags = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(tags), 200


@event_tag_bp.route('/tags/events/<string:tag_name>', methods=['GET'])
def get_events_by_tag(tag_name):
    """
    GET /events/tags/events/<tag_name> - Get all events with a specific tag.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT e.* FROM Event e
            INNER JOIN Event_Tag et ON e.event_id = et.event_id
            INNER JOIN Tag t ON et.tag_id = t.tag_id
            WHERE t.tag_name = %s
            """
            cursor.execute(sql, (tag_name,))
            events = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(events), 200


@event_tag_bp.route('/tags/popular', methods=['GET'])
def get_popular_tags():
    """
    GET /events/tags/popular - Retrieve popular tags based on usage.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT t.tag_name, COUNT(et.tag_id) AS usage_count
            FROM Tag t
            INNER JOIN Event_Tag et ON t.tag_id = et.tag_id
            GROUP BY t.tag_id
            ORDER BY usage_count DESC
            LIMIT 10
            """
            cursor.execute(sql)
            tags = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(tags), 200


@event_tag_bp.route('/<int:event_id>/tags', methods=['PUT'])
@jwt_required
def update_event_tags(event_id):
    """
    PUT /events/tags/<event_id> - Update tags for a specific event.
    Expects JSON: { "tags": ["tag1", "tag2"] }
    """
    data = request.get_json() or {}
    tags = data.get('tags', [])

    if not tags:
        return jsonify({"error": "Tags are required."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Clear existing tags
            sql_clear = """
            DELETE FROM Event_Tag WHERE event_id = %s
            """
            cursor.execute(sql_clear, (event_id,))

            # Add new tags
            for tag in tags:
                sql_tag = """
                INSERT INTO Tag (tag_name) VALUES (%s) ON DUPLICATE KEY UPDATE tag_id=LAST_INSERT_ID(tag_id)
                """
                cursor.execute(sql_tag, (tag,))
                tag_id = cursor.lastrowid

                sql_event_tag = """
                INSERT INTO Event_Tag (event_id, tag_id) VALUES (%s, %s)
                """
                cursor.execute(sql_event_tag, (event_id, tag_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Tags updated successfully."}), 200


@event_tag_bp.route('/tags/<int:event_id>', methods=['DELETE'])
@jwt_required
def delete_event_tags(event_id):
    """
    DELETE /events/tags/<event_id> - Remove all tags for a specific event.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            DELETE FROM Event_Tag WHERE event_id = %s
            """
            cursor.execute(sql, (event_id,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Tags removed successfully."}), 200
