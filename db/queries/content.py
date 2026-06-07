from db.connection import get_connection

def set_contents_pending():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE content
            SET status_id = (SELECT id FROM status WHERE name = 'pending')
            WHERE status_id IN (
                SELECT id FROM status WHERE name IN ('running', 'failed')
            )
        """)
        conn.commit()
    finally:
        conn.close()

def get_pending_content_ids(fetcher_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id FROM content c
            JOIN link l ON l.id = c.link_id
            WHERE l.fetcher_id = %s
            AND c.status_id = (SELECT id FROM status WHERE name = 'pending')
        """, (fetcher_id,))
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def update_content(content_id, content, status):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE content
            SET content = %s,
                status_id = (SELECT id FROM status WHERE name = %s)
            WHERE id = %s
        """, (content, status, content_id))
        if status == 'completed':
            cur.execute("""
                INSERT INTO embedding (content_id, status_id)
                VALUES (%s, (SELECT id FROM status WHERE name = 'pending'))
                ON CONFLICT (content_id) DO NOTHING
            """, (content_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_content_url(content_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.url FROM link l
            JOIN content c ON c.link_id = l.id
            WHERE c.id = %s
        """, (content_id,))
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        conn.close()