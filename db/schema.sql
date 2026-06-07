CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS status (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS config (
    id SERIAL PRIMARY KEY,
    hash VARCHAR(64) NOT NULL UNIQUE,
    embedding_hash VARCHAR(64),
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
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (fetcher_id, url)
);

CREATE TABLE IF NOT EXISTS content (
    id SERIAL PRIMARY KEY,
    link_id INTEGER NOT NULL REFERENCES link(id) ON DELETE CASCADE,
    content TEXT,
    status_id INTEGER NOT NULL REFERENCES status(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (link_id)
);

CREATE TABLE IF NOT EXISTS embedding (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    embedding VECTOR(1024),
    status_id INTEGER NOT NULL REFERENCES status(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (content_id)
);

CREATE INDEX ON link (fetcher_id);
CREATE INDEX ON config (hash);
CREATE INDEX ON content (link_id);
CREATE INDEX ON content (status_id);
CREATE INDEX ON embedding (content_id);
CREATE INDEX ON embedding (status_id);
