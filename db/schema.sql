CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS status (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS config (
    id SERIAL PRIMARY KEY,
    hash VARCHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fetcher (
    id SERIAL PRIMARY KEY,
    config_id INTEGER NOT NULL REFERENCES config(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    UNIQUE (config_id, url)
);

CREATE TABLE IF NOT EXISTS link (
    id SERIAL PRIMARY KEY,
    fetcher_id INTEGER NOT NULL REFERENCES fetcher(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', coalesce(content, ''))) STORED,
    embedding VECTOR(1024),
    status_id INTEGER NOT NULL REFERENCES status(id),
    UNIQUE (fetcher_id, url),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON link (fetcher_id);
CREATE INDEX ON link (status_id);
CREATE INDEX ON config (hash);
CREATE INDEX ON link USING gin(content_tsv);
