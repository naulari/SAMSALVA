DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Friends;
DROP TABLE IF EXISTS Albums;
DROP TABLE IF EXISTS Photos;
DROP TABLE IF EXISTS Comments;
DROP TABLE IF EXISTS Tags;
DROP TABLE IF EXISTS PictureHasTag;
CREATE TABLE Users (
    user_id INT NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    dob VARCHAR(255),
    hometown VARCHAR(255),
    gender VARCHAR(10),
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id),
    CONSTRAINT email_check CHECK (email LIKE '%@%'),
    CONSTRAINT password_lenCheck CHECK (LENGTH(password) >= 6)
);
CREATE TABLE Friends (
    user_id INT,
    friend_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (friend_id) REFERENCES Users(user_id)
);
CREATE TABLE Albums (
    album_id INT NOT NULL UNIQUE,
    album_name VARCHAR(255) NOT NULL,
    user_id INT,
    create_date VARCHAR(255),
    PRIMARY KEY (album_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
CREATE TABLE Photos (
    photo_id INT NOT NULL UNIQUE,
    caption VARCHAR(255),
    photo_path VARCHAR(255),
    album_id INT,
    user_id INT,
    PRIMARY KEY (photo_id),
    FOREIGN KEY (album_id) REFERENCES Albums(album_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
CREATE TABLE Comments (
    comment_id INT NOT NULL UNIQUE,
    comment_text VARCHAR(255) NOT NULL,
    photo_id INT,
    user_id INT,
    PRIMARY KEY (comment_id),
    FOREIGN KEY (photo_id) REFERENCES Photos(photo_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
CREATE TABLE Tags (
    tag_id INT NOT NULL UNIQUE,
    tag_description VARCHAR(255) NOT NULL,
    photo_id INT NOT NULL,
    CONSTRAINT lower_case CHECK (tag_description = LOWER(tag_description)),
    CONSTRAINT no_spaces CHECK (tag_description NOT LIKE '% %'),
    PRIMARY KEY (tag_id)
    FOREIGN KEY (photo_id) REFERENCES Photos(photo_id)
);

CREATE TABLE PictureHasLikes (
    photo_id INT,
    user_id INT,
    FOREIGN KEY (photo_id) REFERENCES Photos(photo_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);