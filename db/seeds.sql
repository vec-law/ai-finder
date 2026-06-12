INSERT INTO status (name) VALUES ('pending'), ('running'), ('completed'), ('failed') ON CONFLICT (name) DO NOTHING;
INSERT INTO fetcher (name) VALUES ('curl') ON CONFLICT (name) DO NOTHING;
INSERT INTO page_type (name) VALUES ('paginated') ON CONFLICT (name) DO NOTHING;
