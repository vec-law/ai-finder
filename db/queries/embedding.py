from db.connection import get_connection

def set_embeddings_pending():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE embedding
            SET status_id = (SELECT id FROM status WHERE name = 'pending')
            WHERE status_id IN (
                SELECT id FROM status WHERE name IN ('running', 'failed')
            )
        """)
        conn.commit()
    finally:
        conn.close()

def get_pending_embedding_ids(fetcher_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id FROM embedding e
            JOIN content c ON c.id = e.content_id
            JOIN link l ON l.id = c.link_id
            WHERE l.fetcher_id = %s
            AND e.status_id = (SELECT id FROM status WHERE name = 'pending')
        """, (fetcher_id, ))
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def get_embedding_content(embedding_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.content FROM content c
            JOIN embedding e ON e.content_id = c.id
            WHERE e.id = %s
        """, (embedding_id,))
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def update_embedding(embedding_id, embedding, status):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE embedding
            SET embedding = %s,
                status_id = (SELECT id FROM status WHERE name = %s)
            WHERE id = %s
        """, (embedding, status, embedding_id))
        conn.commit()
        return True
    finally:
        conn.close()
