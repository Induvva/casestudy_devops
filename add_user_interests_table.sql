-- Migration script to add user_interests table
CREATE TABLE IF NOT EXISTS user_interests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    interest TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username)
);
