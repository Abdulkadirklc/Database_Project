import pymysql

# Database configuration
DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'event_management'

# Function to execute SQL statements
def execute_sql_statements(statements, connection):
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
        connection.commit()

# SQL Statements to create the schema
CREATE_DATABASE = f"""
CREATE DATABASE IF NOT EXISTS {DB_NAME} 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;
"""

CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS `User` (
        user_id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(30) NOT NULL UNIQUE,
        email VARCHAR(30) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        bio VARCHAR(255)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS `Group` (
        group_id INT PRIMARY KEY AUTO_INCREMENT,
        group_name VARCHAR(30) NOT NULL,
        group_description TEXT,
        created_by INT,
        FOREIGN KEY (created_by) REFERENCES `User`(user_id) ON DELETE SET NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Membership (
        membership_id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT,
        group_id INT,
        user_role ENUM('Member', 'Admin', 'Guest') NOT NULL,
        FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
        UNIQUE (user_id, group_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS `Event` (
        event_id INT PRIMARY KEY AUTO_INCREMENT,
        group_id INT,
        event_name VARCHAR(255) NOT NULL,
        event_description TEXT,
        event_date DATE NOT NULL,
        event_location VARCHAR(255),
        FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Event_Attendance (
        attendance_id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT,
        event_id INT,
        event_status ENUM('Attended', 'Interested', 'Not Attended') NOT NULL,
        FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE,
        FOREIGN KEY (event_id) REFERENCES `Event`(event_id) ON DELETE CASCADE,
        UNIQUE (user_id, event_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Feedback (
        feedback_id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT,
        event_id INT,
        rating INT CHECK (rating >= 1 AND rating <= 5),
        feedback TEXT,
        FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE,
        FOREIGN KEY (event_id) REFERENCES `Event`(event_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Message_Board (
        message_id INT PRIMARY KEY AUTO_INCREMENT,
        group_id INT,
        user_id INT,
        user_message TEXT NOT NULL,
        message_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE SET NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Tag (
        tag_id INT PRIMARY KEY AUTO_INCREMENT,
        tag_name VARCHAR(32) NOT NULL UNIQUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Event_Tag (
        event_id INT,
        tag_id INT,
        FOREIGN KEY (event_id) REFERENCES `Event`(event_id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES Tag(tag_id) ON DELETE CASCADE,
        PRIMARY KEY (event_id, tag_id)
    );
    """
]
 
CREATE_TRIGGERS = [
    """
    CREATE TRIGGER before_event_insert
    BEFORE INSERT ON `Event`
    FOR EACH ROW
    BEGIN
        DECLARE group_exists INT;

        -- Check if the group exists in the Group table
        SELECT COUNT(*) INTO group_exists
        FROM `Group`
        WHERE group_id = NEW.group_id;

        -- If the group does not exist, raise an error
        IF group_exists = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The specified group does not exist';
        END IF;
    END;
    """,
    """
    CREATE TRIGGER before_membership_insert
    BEFORE INSERT ON `Membership`
    FOR EACH ROW
    BEGIN
        DECLARE group_creator INT;

        -- Get the group creator from Group table
        SELECT created_by INTO group_creator
        FROM `Group`
        WHERE group_id = NEW.group_id;
        
        -- Check if the user is the creator of the group
        IF group_creator = NEW.user_id THEN
            -- If the user is the creator, set the role to 'Admin'
            SET NEW.user_role = 'Admin';
        END IF;
    END;
    """,
    """
    CREATE TRIGGER before_message_insert
    BEFORE INSERT ON Message_Board
    FOR EACH ROW
    BEGIN
        DECLARE is_member INT;

        -- Check if the user is a member of the group
        SELECT COUNT(*)
        INTO is_member
        FROM Membership
        WHERE user_id = NEW.user_id
          AND group_id = NEW.group_id;

        -- If the user is not a member, raise an error
        IF is_member = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'User must be a member of the group to post a message.';
        END IF;
    END;
    """,
    """
    CREATE TRIGGER before_user_update
    BEFORE UPDATE ON `User`
    FOR EACH ROW
    BEGIN
        -- Check if the new and old usernames are the same
        IF NEW.username <> OLD.username THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Username change is not allowed.';
        END IF;
    END;
    """,
    """
    CREATE TRIGGER before_feedback_insert
    BEFORE INSERT ON Feedback
    FOR EACH ROW
    BEGIN
        DECLARE user_attended INT;

        -- Check if the comment is empty
        IF (NEW.feedback IS NULL OR NEW.feedback = '') THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Feedback comments are required.';
        END IF;

        -- Check if the user attended the event
        SELECT COUNT(*)
        INTO user_attended
        FROM Event_Attendance e_a
        WHERE e_a.user_id = NEW.user_id
          AND event_id = NEW.event_id 
          AND event_status = 'Attended';

        IF user_attended = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'User must have attended the event to provide feedback.';
        END IF;
    END;
    """,
    """
    CREATE TRIGGER before_event_insert_past_check
    BEFORE INSERT ON `Event`
    FOR EACH ROW
    BEGIN
        IF NEW.event_date < CURDATE() THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Event date cannot be in the past.';
        END IF;
    END;
    """,
    """
    CREATE TRIGGER before_user_insert
    BEFORE INSERT ON `User`
    FOR EACH ROW
    BEGIN
        IF NEW.bio IS NULL OR NEW.bio = '' THEN
            SET NEW.bio = 'A bio hasn’t been set yet, but we’re sure this individual has a great story to share!';
        END IF;
    END;
    """
]

def main():
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            cursorclass=pymysql.cursors.DictCursor
        )

        print("Connected to MySQL server.")

        # Create the database
        with connection.cursor() as cursor:
            cursor.execute(CREATE_DATABASE)
        print(f"Database '{DB_NAME}' created or already exists.")

        # Explicitly select the database
        connection.select_db(DB_NAME)

        # Create the tables
        print("Creating tables...")
        execute_sql_statements(CREATE_TABLES, connection)

        # Create the triggers
        print("Creating triggers...")
        execute_sql_statements(CREATE_TRIGGERS, connection)

        print("All tables and triggers created successfully.")

    except pymysql.MySQLError as e:
        print(f"Error: {e}")

    finally:
        if connection:
            connection.close()
            print("Connection closed.")


if __name__ == "__main__":
    main()
