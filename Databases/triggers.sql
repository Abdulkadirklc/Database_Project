DELIMITER //

-- This trigger are used to prevent unauthorized groups to create events
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

-- Trigger to prevent changing username
CREATE TRIGGER before_user_update
BEFORE UPDATE ON `User`
FOR EACH ROW
BEGIN
    -- Check if the new and old usernames are the same
    IF NEW.username <> OLD.username THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Username change is not allowed.';
    END IF;
END//


-- Trigger to ensure before inserting feedback, the user attended the event 
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
    FROM Event_Attendance e_a
    WHERE e_a.user_id = NEW.user_id
      AND event_id = NEW.event_id 
      AND event_status = 'Attended';

    IF user_attended = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User must have attended the event to provide feedback.';
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