from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

event_bp = Blueprint('event_bp', __name__)

default_event_description = "There is no description yet for this event."


# Check if the request sender is in the group
@event_bp.route('/', methods=['POST'])
@jwt_required
def create_event():
    """
    POST /events - Create a new event.
    Expects JSON: { "group_id": int, "event_name": str, "event_date": str, "event_location": str, "event_description": str (optional) }
    """
    data = request.get_json() or {}
    required_fields = ['group_id', 'event_name', 'event_date', 'event_location']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields."}), 400

    group_id = data['group_id']
    user_id = g.current_user_id
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_check_membership = """
            SELECT COUNT(*) FROM Membership WHERE group_id = %s AND user_id = %s
            """
            cursor.execute(sql_check_membership, (group_id, user_id))
            is_member = cursor.fetchone()['COUNT(*)']
            if not is_member:
                return jsonify({"error": "You are not a member of this group."}), 403

            # Proceed with event creation
            event_description = data.get('event_description', default_event_description)
            sql = """
            INSERT INTO Event (group_id, event_name, event_description, event_date, event_location)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['group_id'],
                data['event_name'],
                event_description,
                data['event_date'],
                data['event_location']
            ))
            conn.commit()
            event_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({"message": "Event created successfully.", "event_id": event_id}), 201


@event_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required
def update_event(event_id):
    """
    PUT /events/<event_id> - Update an event by its ID.
    """
    data = request.get_json() or {}
    user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the user is a member of the group hosting the event
            sql_check_group = """
            SELECT group_id FROM Event WHERE event_id = %s
            """
            cursor.execute(sql_check_group, (event_id,))
            event = cursor.fetchone()
            if not event:
                return jsonify({"error": "Event not found."}), 404

            sql_check_membership = """
            SELECT COUNT(*) FROM Membership WHERE group_id = %s AND user_id = %s
            """
            cursor.execute(sql_check_membership, (event['group_id'], user_id))
            is_member = cursor.fetchone()['COUNT(*)']
            if not is_member:
                return jsonify({"error": "You are not a member of the group hosting this event."}), 403

            # Proceed with event update
            sql_update = """
            UPDATE Event
            SET event_name = %s, event_description = %s, event_date = %s, event_location = %s
            WHERE event_id = %s
            """
            cursor.execute(sql_update, (
                data.get('event_name'),
                data.get('event_description'),
                data.get('event_date'),
                data.get('event_location'),
                event_id
            ))
            conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Event updated successfully."}), 200


@event_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required
def delete_event(event_id):
    """
    DELETE /events/<event_id> - Delete an event by its ID.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            DELETE FROM Event WHERE event_id = %s
            """
            cursor.execute(sql, (event_id,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Event deleted successfully."}), 200


@event_bp.route('/user/groups', methods=['GET'])
@jwt_required
def get_user_group_events():
    """
    GET /events/user/groups - Retrieve events for all groups the user belongs to.
    """
    user_id = g.current_user_id

    if not user_id:
        return jsonify({"error": "User ID not found in request context."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the user is in any groups
            sql_check_membership = """
            SELECT COUNT(*) AS group_count FROM Membership WHERE user_id = %s
            """
            cursor.execute(sql_check_membership, (user_id,))
            group_count = cursor.fetchone()['group_count']
            
            if group_count == 0:
                return jsonify({"message": "User is not a member of any group.", "events": []}), 200

            # Retrieve events for all groups the user belongs to
            sql = """
            SELECT e.event_id, e.group_id, e.event_name, e.event_date, e.event_location, e.event_description
            FROM Event e
            INNER JOIN Membership m ON e.group_id = m.group_id
            WHERE m.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            events = cursor.fetchall()

            # Debug log if no events are found
            if not events:
                return jsonify({"message": "No events found for the user's groups.", "events": []}), 200

    except Exception as e:
        # Log and return any unexpected errors
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify(events), 200


@event_bp.route('/sorted', methods=['GET'])
def sort_events_by_time():
    """
    GET /events/sorted - Retrieve past and upcoming events separately.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_past = """
            SELECT * FROM Event WHERE event_date < CURDATE()
            """
            sql_future = """
            SELECT * FROM Event WHERE event_date >= CURDATE()
            """
            cursor.execute(sql_past)
            past_events = cursor.fetchall()

            cursor.execute(sql_future)
            future_events = cursor.fetchall()
    finally:
        conn.close()

    return jsonify({"past_events": past_events, "future_events": future_events}), 200


@event_bp.route('/notify', methods=['POST'])
@jwt_required
def notify_message_board():
    """
    POST /events/notify - Notify the message board when an event is created.
    """
    data = request.get_json() or {}
    event_id = data.get('event_id')
    group_id = data.get('group_id')
    user_id = g.current_user_id

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if user is part of the group
            sql_check_membership = """
            SELECT COUNT(*) FROM Membership WHERE group_id = %s AND user_id = %s
            """
            cursor.execute(sql_check_membership, (group_id, user_id))
            is_member = cursor.fetchone()['COUNT(*)']
            if not is_member:
                return jsonify({"error": "You are not a member of this group."}), 403

            # Verify event exists
            sql_event = """
            SELECT event_name FROM Event WHERE event_id = %s
            """
            cursor.execute(sql_event, (event_id,))
            event = cursor.fetchone()
            if not event:
                return jsonify({"error": "Event not found"}), 404

            # Post notification
            sql_message = """
            INSERT INTO Message_Board (group_id, user_id, user_message)
            VALUES (%s, %s, %s)
            """
            message = f"New event created: {event['event_name']}"
            cursor.execute(sql_message, (group_id, user_id, message))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Message posted to the board."}), 201