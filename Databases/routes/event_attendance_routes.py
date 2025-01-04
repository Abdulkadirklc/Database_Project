# 404 not found


from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

event_attendance_bp = Blueprint('event_attendance_bp', __name__)


@event_attendance_bp.route('/events/<int:event_id>/attendance', methods=['POST'])
@jwt_required
def add_attendance(event_id):
    """
    POST /events/<event_id>/attendance
    Adds the current user as "going" or "interested" to an event.
    Example JSON body: { "status": "going" } or { "status": "interested" }
    """
    user_id = g.current_user_id  
    data = request.get_json() or {}
    status = data.get('status')

    if not status:
        return jsonify({"error": "Attendance status is required."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_check = """
            SELECT * FROM Event_Attendance
            WHERE event_id = %s AND user_id = %s
            """
            cursor.execute(sql_check, (event_id, user_id))
            existing = cursor.fetchone()

            if existing:
                return jsonify({"error": "You already have attendance info for this event."}), 400

            sql_insert = """
            INSERT INTO Event_Attendance (event_id, user_id, status)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql_insert, (event_id, user_id, status))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Attendance added successfully"}), 201


@event_attendance_bp.route('/events/<int:event_id>/attendance', methods=['GET'])
def list_attendance_for_event(event_id):
    """
    GET /events/<event_id>/attendance
    Lists which users are attending or interested in a specific event.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT ea.user_id, u.username, ea.status
            FROM Event_Attendance ea
            INNER JOIN Users u ON ea.user_id = u.user_id
            WHERE ea.event_id = %s
            """
            cursor.execute(sql, (event_id,))
            attendance_list = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(attendance_list), 200


@event_attendance_bp.route('/users/<int:user_id>/attendance', methods=['GET'])
def list_user_attendance(user_id):
    """
    GET /users/<user_id>/attendance
    Retrieves all events that a particular user is attending or interested in.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT ea.event_id, e.event_name, ea.status, e.event_date
            FROM Event_Attendance ea
            INNER JOIN Event e ON ea.event_id = e.event_id
            WHERE ea.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            user_events = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(user_events), 200


@event_attendance_bp.route('/events/<int:event_id>/attendance', methods=['PUT'])
@jwt_required
def update_attendance(event_id):
    """
    PUT /events/<event_id>/attendance
    Updates the attendance status of the current user for a specific event.
    Example JSON body: { "status": "not_going" }
    """
    user_id = g.current_user_id
    data = request.get_json() or {}
    new_status = data.get('status')

    if not new_status:
        return jsonify({"error": "New attendance status is required."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_update = """
            UPDATE Event_Attendance
            SET status = %s
            WHERE event_id = %s AND user_id = %s
            """
            cursor.execute(sql_update, (new_status, event_id, user_id))
            if cursor.rowcount == 0:
                return jsonify({"error": "Attendance record not found."}), 404
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Attendance updated successfully"}), 200


@event_attendance_bp.route('/events/<int:event_id>/attendance', methods=['DELETE'])
@jwt_required
def delete_attendance(event_id):
    """
    DELETE /events/<event_id>/attendance
    Deletes the attendance record of the current user for a specific event.
    """
    user_id = g.current_user_id
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_delete = """
            DELETE FROM Event_Attendance
            WHERE event_id = %s AND user_id = %s
            """
            cursor.execute(sql_delete, (event_id, user_id))
            if cursor.rowcount == 0:
                return jsonify({"error": "Attendance record not found or already deleted."}), 404
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Attendance deleted successfully"}), 200


@event_attendance_bp.route('/events/attendance/top-users', methods=['GET'])
def get_top_users():
    """
    GET /events/attendance/top-users
    Retrieves a list of users who have attended (or shown interest in) the most events.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT ea.user_id, u.username, COUNT(*) AS total_attendance
            FROM Event_Attendance ea
            INNER JOIN Users u ON ea.user_id = u.user_id
            GROUP BY ea.user_id
            ORDER BY total_attendance DESC
            LIMIT 10
            """
            cursor.execute(sql)
            result = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(result), 200
