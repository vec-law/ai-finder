from db.connection import get_connection

def set_embedding_pending(page_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO embedding (content_id, status_id)
            SELECT c.id, (SELECT id FROM status WHERE name = 'pending')
            FROM content c
            JOIN link l ON l.id = c.link_id
            WHERE l.page_id = %s
            AND c.status_id = (SELECT id FROM status WHERE name = 'completed')
            AND c.content IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM embedding e WHERE e.content_id = c.id
            )
        """, (page_id,))
        cur.execute("""
            UPDATE embedding
            SET status_id = (SELECT id FROM status WHERE name = 'pending')
            WHERE content_id IN (
                SELECT c.id FROM content c
                JOIN link l ON l.id = c.link_id
                WHERE l.page_id = %s
                AND c.status_id = (SELECT id FROM status WHERE name = 'completed')
                AND c.content IS NOT NULL
            )
            AND status_id != (SELECT id FROM status WHERE name = 'completed')
        """, (page_id,))
        cur.execute("""
            UPDATE embedding
            SET status_id = (SELECT id FROM status WHERE name = 'pending')
            WHERE content_id IN (
                SELECT c.id FROM content c
                JOIN link l ON l.id = c.link_id
                WHERE l.page_id = %s
                AND c.status_id = (SELECT id FROM status WHERE name = 'completed')
                AND c.content IS NOT NULL
            )
            AND status_id = (SELECT id FROM status WHERE name = 'completed')
            AND embedding IS NULL
        """, (page_id,))
        conn.commit()
    finally:
        conn.close()

def get_embedding_ids(page_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id FROM embedding e
            JOIN content c ON c.id = e.content_id
            JOIN link l ON l.id = c.link_id
            WHERE l.page_id = %s
            AND e.status_id = (SELECT id FROM status WHERE name = 'pending')
        """, (page_id,))
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def get_embedding_context(embedding_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.content, s.name, l.title, l.url FROM embedding e
            JOIN content c ON c.id = e.content_id
            JOIN status s ON s.id = c.status_id
            JOIN link l ON l.id = c.link_id
            WHERE e.id = %s
        """, (embedding_id,))
        row = cur.fetchone()
        return row if row else None
    finally:
        conn.close()

def update_embedding(embedding_id, embedding_str, status):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE embedding
            SET embedding = %s::vector,
                status_id = (SELECT id FROM status WHERE name = %s)
            WHERE id = %s
        """, (embedding_str, status, embedding_id))
        conn.commit()
        return True
    finally:
        conn.close()
