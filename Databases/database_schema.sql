-- Create the database
CREATE DATABASE IF NOT EXISTS event_management 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Use the created database
USE event_management;

-- Set default storage engine to InnoDB, it supports foreign keys
SET default_storage_engine = 'InnoDB';

-- User table: Contains a unique identifier for each user and necessary fields
-- I am using `User` as the table name, becasue user is a reserved keyword in some databases.
CREATE TABLE `User` (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(30) NOT NULL UNIQUE,
    password VARCHAR(20) NOT NULL,
    bio VARCHAR(255)
);

-- Group table: Contains a unique identifier for each group and a reference to the group creator
CREATE TABLE `Group` (
    group_id INT PRIMARY KEY AUTO_INCREMENT,
    group_name VARCHAR(30) NOT NULL,
    group_description TEXT,
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES `User`(user_id) ON DELETE SET NULL
);

-- Membership table: Holds the membership relationships of users to groups
CREATE TABLE Membership (
    membership_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    group_id INT,
    user_role ENUM('Member', 'Admin','Guest') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    UNIQUE (user_id, group_id)  -- A user can only join a group once
);

-- Event table: Stores events associated with groups
CREATE TABLE `Event` (
    event_id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT,
    event_name VARCHAR(255) NOT NULL,
    event_description TEXT,
    event_date DATE NOT NULL,
    event_location VARCHAR(255),
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE
);

-- Event Attendance table: Tracks users` attendance status for events
CREATE TABLE Event_Attendance (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    event_id INT,
    event_status ENUM('Attended', 'Interested', 'Not Attended') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES `Event`(event_id) ON DELETE CASCADE,
    UNIQUE (user_id, event_id)  -- Each user can only respond to an event once
);

-- Feedback table: Holds feedback provided by users for events
CREATE TABLE Feedback (
    feedback_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    event_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    -- Delete feedback if the associated user or event is deleted
    FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES `Event`(event_id) ON DELETE CASCADE
);

-- Message Board table: Stores messages shared on the message board within groups
CREATE TABLE Message_Board (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT,
    user_id INT,
    user_message TEXT NOT NULL,
    message_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Delete messages if the associated group is deleted
    FOREIGN KEY (group_id) REFERENCES `Group`(group_id) ON DELETE CASCADE,
    -- Set user_id to NULL if the associated user is deleted
    FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE SET NULL
);

-- Tag table: Contains tags that can be used to categorize events
CREATE TABLE Tag (
    tag_id INT PRIMARY KEY AUTO_INCREMENT,
    tag_name VARCHAR(32) NOT NULL UNIQUE
);

-- Event-Tag relationship table: Many-to-many relationship table that associates events with tags
CREATE TABLE Event_Tag (
    event_id INT,
    tag_id INT,
    -- Delete the Event-Tag relationship if the associated event or tag is deleted
    FOREIGN KEY (event_id) REFERENCES `Event`(event_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES Tag(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, tag_id)  -- An event and tag pair must be unique
);