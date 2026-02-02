CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS post (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp INT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES message (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE IF NOT EXISTS notification (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    post_id TEXT NOT NULL,
    content TEXT NOT NULL,
    mentioned_user_id TEXT NOT NULL,
    timestamp INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (post_id) REFERENCES message (id),
    FOREIGN KEY (mentioned_user_id) REFERENCES user (id)
);
