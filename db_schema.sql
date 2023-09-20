CREATE TABLE IF NOT EXISTS metadata(
    "name" VARCHAR(100) PRIMARY KEY,
    extension VARCHAR(55) NOT NULL,
    size INTEGER NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);