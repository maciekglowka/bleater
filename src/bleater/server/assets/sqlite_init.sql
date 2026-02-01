CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS message (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp INT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES message (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
);
