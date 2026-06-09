from db.connection import get_connection

def get_config_id(config_hash):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM config
            WHERE hash = %s
        """, (config_hash,))
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def add_config(config_hash, embedding_config_hash):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO config (hash, embedding_hash)
            VALUES (%s, %s)
            RETURNING id
        """, (config_hash, embedding_config_hash))
        conn.commit()
        return cur.fetchone()[0]
    finally:
        conn.close()

def get_embedding_config(config_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT embedding_hash FROM config
            WHERE id = %s
        """, (config_id,))
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def set_embedding_config(config_id, embedding_hash, vector_size):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM embedding
            WHERE content_id IN (
                SELECT c.id FROM content c
                JOIN link l ON l.id = c.link_id
                JOIN fetcher f ON f.id = l.fetcher_id
                WHERE f.config_id = %s
            )
        """, (config_id,))
        cur.execute(f"""
            ALTER TABLE embedding
            ALTER COLUMN embedding TYPE vector({vector_size})
        """)
        cur.execute("""
            UPDATE config
            SET embedding_hash = %s
            WHERE id = %s
        """, (embedding_hash, config_id))
        cur.execute("""
            INSERT INTO embedding (content_id, status_id)
            SELECT c.id, (SELECT id FROM status WHERE name = 'pending')
            FROM content c
            JOIN link l ON l.id = c.link_id
            JOIN fetcher f ON f.id = l.fetcher_id
            WHERE f.config_id = %s
            AND c.status_id = (SELECT id FROM status WHERE name = 'completed')
            ON CONFLICT (content_id) DO NOTHING
        """, (config_id,))
        conn.commit()
    finally:
        conn.close()
        
