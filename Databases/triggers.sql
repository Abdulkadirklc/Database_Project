-- This triggers are used to prevent unauthorized users from creating events in the database.
DELIMITER //

CREATE TRIGGER before_event_insert
BEFORE INSERT ON `Event`
FOR EACH ROW
BEGIN
    DECLARE user_role ENUM('Member', 'Admin', 'Guest');
    DECLARE group_creator INT;
    
    -- Get the group creator from Group table
    SELECT created_by INTO group_creator
    FROM `Group`
    WHERE group_id = NEW.group_id;
    
    -- Get the user role from Membership table
    SELECT user_role INTO user_role
    FROM Membership
    WHERE user_id = NEW.created_by AND group_id = NEW.group_id
    LIMIT 1;
    
    -- If the user is not an admin or the creator of the group, prevent the insert
    IF user_role != 'Admin' AND group_creator != NEW.created_by THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only the group admin or the group creator can create events';
    END IF;
END //


-- This trigger is used to automatically assign the role of 'Admin' to the group creator when joining a group.

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
END //


-- Check if User is in the Group Before Inserting a Message
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
END//


-- Check if the user has permission to delete the message 
CREATE TRIGGER before_message_delete
BEFORE DELETE ON Message_Board
FOR EACH ROW
BEGIN
    DECLARE user_role ENUM('Member', 'Admin', 'Guest');

    -- Check the user's role in the group
    SELECT user_role INTO user_role
    FROM Membership
    WHERE user_id = @current_user_id AND group_id = OLD.group_id;

    -- Ensure the user has permission to delete
    IF (@current_user_id <> OLD.user_id AND user_role <> 'Admin') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only the message author or an admin can delete this message.';
    END IF;
END//


-- This trigger ensures that only the message author can update the message
CREATE TRIGGER before_message_update
BEFORE UPDATE ON Message_Board
FOR EACH ROW
BEGIN
    -- Check if the current user is the author of the message
    IF OLD.user_id <> @current_user_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only the message author can update this message.';
    END IF;
END//


-- Trigger to ensure only the user can delete their account
CREATE TRIGGER before_user_delete
BEFORE DELETE ON `User`
FOR EACH ROW
BEGIN
    IF OLD.user_id <> @current_user_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only the user themselves can delete their account.';
    END IF;
END//

-- Trigger to ensure only the user can update their account information
CREATE TRIGGER before_user_update
BEFORE UPDATE ON `User`
FOR EACH ROW
BEGIN
    -- Check if only the user themselves can update their info
    IF OLD.user_id <> @current_user_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only the user themselves can update their account information.';
    END IF;

    -- Check if the new and old usernames are the same
    IF NEW.username <> OLD.username THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Username change is not allowed unless explicitly intended.';
    END IF;
END//


-- Trigger to ensure only an Admin can delete the group
CREATE TRIGGER before_group_delete
BEFORE DELETE ON `Group`
FOR EACH ROW
BEGIN
    DECLARE is_admin INT;

    -- Check if the user trying to delete is an admin in the Membership table
    SELECT COUNT(*)
    INTO is_admin
    FROM Membership
    WHERE group_id = OLD.group_id AND user_id = @current_user_id AND user_role = 'Admin';

    IF is_admin = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only an admin can delete this group.';
    END IF;
END//



-- Trigger to ensure only an Admin can update a group
CREATE TRIGGER before_group_update
BEFORE UPDATE ON `Group`
FOR EACH ROW
BEGIN
    DECLARE is_admin INT;

    -- Check if the user trying to update is an admin in the Membership table
    SELECT COUNT(*)
    INTO is_admin
    FROM Membership
    WHERE group_id = NEW.group_id AND user_id = @current_user_id AND user_role = 'Admin';

    IF is_admin = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only an admin can update this group.';
    END IF;
END//


-- Trigger to ensure before inserting feedback, the user attended the event and is the author, 
-- and the feedback in not null
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
    FROM Event_Attendance
    WHERE user_id = @current_user_id 
      AND event_id = NEW.event_id 
      AND event_status = 'Attended';

    IF user_attended = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User must have attended the event to provide feedback.';
    END IF;
END//

-- Trigger to ensure before deleting feedback, the user is either the author of the feedback or an admin
CREATE TRIGGER before_feedback_delete
BEFORE DELETE ON Feedback
FOR EACH ROW
BEGIN
    DECLARE is_admin INT DEFAULT 0;
    -- Check if the authenticated user is the author of the feedback
    IF @current_user_id <> OLD.user_id THEN
        -- Check if authenticated user is an Admin in the Membership table
        SELECT COUNT(*)
        INTO is_admin
        FROM Membership
        WHERE user_id = @current_user_id 
          AND group_id = (
            SELECT group_id FROM Event WHERE event_id = OLD.event_id
          )  
          AND user_role = 'Admin';

        -- If neither condition is met, raise an error
        IF is_admin = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only the author or an admin can delete this feedback.';
        END IF;
    END IF;
END//

-- Trigger to ensure before updating feedback, only the author can modify it
CREATE TRIGGER before_feedback_update
BEFORE UPDATE ON Feedback
FOR EACH ROW
BEGIN
    -- Ensure that only the author of the feedback can modify it
    IF @current_user_id <> NEW.user_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Only the author of the feedback can update it.';
    END IF;
END//

-- Trigger to prevent event creation in the past
CREATE TRIGGER before_event_insert
BEFORE INSERT ON `Event`
FOR EACH ROW
BEGIN
    IF NEW.event_date < CURDATE() THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Event date cannot be in the past.';
    END IF;
END//

-- Trigger to set up a default bio if not provided.
CREATE TRIGGER before_user_insert
BEFORE INSERT ON `User`
FOR EACH ROW
BEGIN
    IF NEW.bio IS NULL OR NEW.bio = '' THEN
        SET NEW.bio = 'A bio hasn’t been set yet, but we’re sure this individual has a great story to share!';
    END IF;
END//


DELIMITER ;