# Table/column name hataları
# Delete feedback, ya sadece user kendi feedbackini silebilsin ya da group admine çevir even owner'ı

from flask import Blueprint, request, jsonify, g
from routes import get_connection
from routes.auth import jwt_required

feedback_bp = Blueprint('feedback_bp', __name__)

@feedback_bp.route('/', methods=['POST'])
@jwt_required
def add_feedback():
    """
    POST /feedback
    Adds feedback from a user for a specific event.
    Example JSON body: { "event_id": 1, "rating": 5, "feedback": "Great event!" }
    """
    user_id = g.current_user_id
    data = request.get_json() or {}
    event_id = data.get('event_id')
    rating = data.get('rating')
    feedback = data.get('feedback', "")

    if not event_id or rating is None:
        return jsonify({"error": "event_id and rating are required."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_insert = """
            INSERT INTO Feedback (event_id, user_id, rating, feedback)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (event_id, user_id, rating, feedback))
            conn.commit()
            feedback_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({"message": "Feedback added successfully", "feedback_id": feedback_id}), 201


@feedback_bp.route('/events/<int:event_id>', methods=['GET'])
def get_feedback_by_event(event_id):
    """
    GET /feedback/events/<event_id>
    Retrieves all feedback for a specific event.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT f.feedback_id, f.user_id, u.username, f.rating, f.feedback
            FROM Feedback f
            INNER JOIN User u ON f.user_id = u.user_id
            WHERE f.event_id = %s
            """
            cursor.execute(sql, (event_id,))
            feedbacks = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(feedbacks), 200


@feedback_bp.route('/users/<int:user_id>', methods=['GET'])
def get_feedback_by_user(user_id):
    """
    GET /feedback/users/<user_id>
    Retrieves all feedback created by a specific user.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT f.feedback_id, f.event_id, e.event_name, f.rating, f.feedback
            FROM Feedback f
            INNER JOIN Event e ON f.event_id = e.event_id
            WHERE f.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            feedbacks = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(feedbacks), 200


@feedback_bp.route('/stars/<int:event_id>', methods=['GET'])
def get_event_rating_summary(event_id):
    """
    GET /feedback/stars/<event_id>
    Returns the average rating and total feedback count for a specific event.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT AVG(rating) AS average_rating, COUNT(*) AS total_feedback
            FROM Feedback
            WHERE event_id = %s
            """
            cursor.execute(sql, (event_id,))
            result = cursor.fetchone()
    finally:
        conn.close()

    if not result or result['total_feedback'] == 0:
        return jsonify({"average_rating": 0, "total_feedback": 0}), 200

    return jsonify({
        "average_rating": float(result['average_rating']),
        "total_feedback": int(result['total_feedback'])
    }), 200


@feedback_bp.route('/<int:feedback_id>', methods=['PUT'])
@jwt_required
def update_feedback(feedback_id):
    """
    PUT /feedback/<feedback_id>
    Updates an existing feedback. Only the owner of the feedback can do this.
    Example JSON body: { "rating": 4, "feedback": "It was good, but could be better." }
    """
    user_id = g.current_user_id
    data = request.get_json() or {}
    new_rating = data.get('rating')
    new_feedback = data.get('feedback')

    if new_rating is None:
        return jsonify({"error": "rating is required to update feedback."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the current user is the owner of this feedback
            sql_check_owner = """
            SELECT user_id FROM Feedback WHERE feedback_id = %s
            """
            cursor.execute(sql_check_owner, (feedback_id,))
            feedback = cursor.fetchone()
            if not feedback:
                return jsonify({"error": "Feedback not found."}), 404
            
            if feedback['user_id'] != user_id:
                return jsonify({"error": "You can only update your own feedback."}), 403

            sql_update = """
            UPDATE Feedback
            SET rating = %s, feedback = %s
            WHERE feedback_id = %s
            """
            cursor.execute(sql_update, (new_rating, new_feedback, feedback_id))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Feedback updated successfully"}), 200


@feedback_bp.route('/<int:feedback_id>', methods=['DELETE'])
@jwt_required
def delete_feedback(feedback_id):
    """
    DELETE /feedback/<feedback_id>
    Deletes a feedback. Only the feedback owner or the event creator can do this.
    """
    user_id = g.current_user_id
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql_feedback = """
            SELECT f.user_id, e.group_id, e.event_id
            FROM Feedback f
            INNER JOIN Event e ON f.event_id = e.event_id
            WHERE f.feedback_id = %s
            """
            cursor.execute(sql_feedback, (feedback_id,))
            feedback = cursor.fetchone()
            if not feedback:
                return jsonify({"error": "Feedback not found."}), 404

            feedback_owner_id = feedback['user_id']
            event_id = feedback['event_id']

            sql_event_owner = """
            SELECT created_by FROM Event WHERE event_id = %s
            """
            cursor.execute(sql_event_owner, (event_id,))
            event_data = cursor.fetchone()
            if not event_data:
                return jsonify({"error": "Event not found."}), 404

            if feedback_owner_id != user_id and event_data['created_by'] != user_id:
                return jsonify({"error": "You are not allowed to delete this feedback."}), 403

            sql_delete = """
            DELETE FROM Feedback WHERE feedback_id = %s
            """
            cursor.execute(sql_delete, (feedback_id,))
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Feedback deleted successfully"}), 200

