CREATE TABLE usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    instance_type TEXT,
    count INTEGER,
    account_id INTEGER
);
