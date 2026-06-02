INSERT INTO status (name) VALUES 
    ('pending'),
    ('running'),
    ('completed'),
    ('failed')
ON CONFLICT (name) DO NOTHING;
