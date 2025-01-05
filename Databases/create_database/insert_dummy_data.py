import requests
import csv

BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"Content-Type": "application/json"}

def load_csv_data(file_path):
    """Load data from a CSV file."""
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def register_user(user):
    """Register a new user."""
    response = requests.post(f"{BASE_URL}/users", json=user, headers=HEADERS)
    if response.status_code == 201:
        print(f"User {user['username']} registered successfully.")
    else:
        print(f"Failed to register user {user['username']}: {response.text}")

def login_user(username, password):
    """Log in as a user and return the JWT token."""
    response = requests.post(f"{BASE_URL}/users/login", json={"username": username, "password": password}, headers=HEADERS)
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"Login successful for {username}.")
        return token
    else:
        print(f"Failed to login for {username}: {response.text}")
        return None

def create_group(group, headers):
    """Create a new group."""
    response = requests.post(f"{BASE_URL}/groups", json=group, headers=headers)
    if response.status_code == 201:
        group_id = response.json().get("group_id")
        print(f"Group '{group['group_name']}' created successfully with ID {group_id}.")
        return group_id
    else:
        print(f"Failed to create group '{group['group_name']}': {response.text}")
        return None

def add_user_to_group(group_id, headers):
    """Add the logged-in user to a group as a member."""
    response = requests.post(f"{BASE_URL}/membership/", json={"group_id": group_id}, headers=headers)
    if response.status_code == 201:
        print(f"User added to group {group_id} successfully.")
    else:
        print(f"Failed to add user to group {group_id}: {response.text}")

def create_event(event, headers):
    """Create a new event."""
    response = requests.post(f"{BASE_URL}/events", json=event, headers=headers)
    if response.status_code == 201:
        event_id = response.json().get("event_id")
        print(f"Event '{event['event_name']}' created successfully with ID {event_id}.")
        return event_id
    else:
        print(f"Failed to create event '{event['event_name']}': {response.text}")
        return None

def process_memberships(memberships, users):
    """Process membership additions."""
    for membership in memberships:

        user_id = int(membership["user_id"])
        group_id = int(membership["group_id"])
        user_role = membership["user_role"]

        # Map user_id to the `users` list
        user = users[user_id - 1]  

        # Log in as the user
        token = login_user(user["username"], user["password"])
        if not token:
            print(f"Skipping membership addition for {user['username']} due to login failure.")
            continue

        # Set Authorization header for this user
        HEADERS["Authorization"] = f"Bearer {token}"

        # Add the user to the group
        add_user_to_group(group_id, HEADERS)

def process_events(events, users, groups):
    """Process event creation."""
    for event in events:
        group_index = int(event["group_id"])
        event_name = event["event_name"]
        event_description = event["event_description"]
        event_date = event["event_date"]
        event_location = event["event_location"]


        # Find the creator of the group
        creator_user_id = int(groups[group_index - 1]["created_by"])

        # Map user_id to user data
        creator = users[creator_user_id - 1]

        # Log in as the group creator
        token = login_user(creator["username"], creator["password"])
        if not token:
            print(f"Skipping event creation for {event_name} due to login failure.")
            continue

        # Set Authorization header for this user
        HEADERS["Authorization"] = f"Bearer {token}"

        # Create the event
        create_event({
            "group_id": group_index,
            "event_name": event_name,
            "event_description": event_description,
            "event_date": event_date,
            "event_location": event_location
        }, HEADERS)
    
def process_event_attendance(attendances, users):
    """Process event attendance data."""
    for attendance in attendances:
        user_id = int(attendance["user_id"]) 
        event_id = int(attendance["event_id"])
        event_status = attendance["event_status"]

        user = users[user_id - 1]  # Map user_id to the `users` list

        # Log in as the user
        token = login_user(user["username"], user["password"])
        if not token:
            print(f"Skipping event attendance for {user['username']} due to login failure.")
            continue

        # Set Authorization header for this user
        HEADERS["Authorization"] = f"Bearer {token}"

        # Record attendance
        response = requests.post(
            f"{BASE_URL}/events/{event_id}/attendance",
            json={"status": event_status},
            headers=HEADERS
        )

        if response.status_code == 201:
            print(f"Event attendance recorded for user {user['username']} for event {event_id}.")
        else:
            print(f"Failed to record attendance for user {user['username']} for event {event_id}: {response.text}")

def process_feedback(feedbacks, users):
    """Process feedback for events."""
    for feedback in feedbacks:
        user_id = int(feedback["user_id"])
        event_id = int(feedback["event_id"])
        rating = int(feedback["rating"])
        feedback_text = feedback["feedback"]

        user = users[user_id - 1] 

        # Log in as the user
        token = login_user(user["username"], user["password"])
        if not token:
            print(f"Skipping feedback submission for {user['username']} due to login failure.")
            continue

        # Set Authorization header for this user
        HEADERS["Authorization"] = f"Bearer {token}"

        # Submit feedback
        response = requests.post(
            f"{BASE_URL}/feedback",
            json={"event_id": event_id, "rating": rating, "feedback": feedback_text},
            headers=HEADERS
        )

        if response.status_code == 201:
            print(f"Feedback submitted for user {user['username']} on event {event_id}.")
        else:
            print(f"Failed to submit feedback for user {user['username']} on event {event_id}: {response.text}")
    
def process_message(messages, users):
    """Post messages to the message board."""
    for message in messages:
        group_id = int(message["group_id"])
        user_id = int(message["user_id"])
        user_message = message["user_message"]

        user = users[user_id - 1]  # Map user_id to the `users` list

        # Log in as the user
        token = login_user(user["username"], user["password"])
        if not token:
            print(f"Skipping message posting for {user['username']} due to login failure.")
            continue

        # Set Authorization header for this user
        HEADERS["Authorization"] = f"Bearer {token}"

        # Post the message
        response = requests.post(
            f"{BASE_URL}/messages",
            json={"group_id": group_id, "user_message": user_message},
            headers=HEADERS
        )

        if response.status_code == 201:
            print(f"Message posted by user {user['username']} in group {group_id}.")
        else:
            print(f"Failed to post message for user {user['username']} in group {group_id}: {response.text}")
      
def login_as_any_user(users):
    """Log in as the first user to perform operations requiring random authentication."""
    user = users[0] 
    token = login_user(user["username"], user["password"])
    if not token:
        print(f"Failed to log in as {user['username']}. Cannot proceed with tag operations.")
        return None
    HEADERS["Authorization"] = f"Bearer {token}"
    return token

def add_tags(tags, users):
    """Add tags to the system."""
    if not login_as_any_user(users):
        return

    for tag_name in tags:
        response = requests.post(
            f"{BASE_URL}/tags",
            json=tag_name,
            headers=HEADERS
        )
        tag_name = tag_name["tag_name"]
        if response.status_code == 201:
            print(f"Tag '{tag_name}' added successfully.")
        else:
            print(f"Failed to add tag '{tag_name}': {response.text}")

            
def main():
    # Load data
    users = load_csv_data("data/users.csv")
    groups = load_csv_data("data/groups.csv")
    memberships = load_csv_data("data/memberships.csv")
    events = load_csv_data("data/events.csv")
    attendances = load_csv_data("data/attendances.csv")
    feedbacks = load_csv_data("data/feedbacks.csv")
    messages = load_csv_data("data/messages.csv")
    tags = load_csv_data("data/tags.csv")


    # Insert data using via API
    
    # Register all users
    for user in users:
        register_user(user)

    # Create groups based on the creator
    for group in groups:
        creator_index = int(group["created_by"]) - 1  
        creator = users[creator_index]
        
        # Log in as the group creator
        token = login_user(creator["username"], creator["password"])
        if not token:
            print(f"Skipping group creation for {group['group_name']} due to login failure for {creator['username']}.")
            continue

        # Set Authorization header for this user
        HEADERS["Authorization"] = f"Bearer {token}"

        # Create the group
        create_group(group, HEADERS)

    process_memberships(memberships, users)
    process_events(events, users, groups)
    process_event_attendance(attendances, users)
    process_feedback(feedbacks, users)
    process_message(messages, users)
    add_tags(tags, users)
    

    
if __name__ == "__main__":
    main()
