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
DELIMITER ;
-- To delete the trigger, use the following command:
-- DROP TRIGGER before_event_insert;



-- This trigger is used to automatically assign the role of 'Admin' to the group creator when joining a group.
DELIMITER //

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

DELIMITER ;
-- To delete the trigger, use the following command:
-- DROP TRIGGER before_membership_insert;



-- Eklenecekler:
-- Sadece o gruba üye olan kişi message boarda mesaj yazabilsin
-- Feedback tablosuna sadece o evente katılan kişiler feedback verebilsin.