from db.connection import get_connection

def get_content_url(content_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.url FROM content c
            JOIN link l ON l.id = c.link_id
            WHERE c.id = %s
        """, (content_id,))
        row = cur.fetchone()
        return row[0] if row else None
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
        conn.commit()
        return True
    finally:
        conn.close()

def get_content_ids(page_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id FROM content c
            JOIN link l ON l.id = c.link_id
            WHERE l.page_id = %s
            AND c.status_id = (SELECT id FROM status WHERE name = 'pending')
        """, (page_id,))
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def set_content_pending(page_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO content (link_id, status_id)
            SELECT l.id, (SELECT id FROM status WHERE name = 'pending')
            FROM link l
            WHERE l.page_id = %s
            AND NOT EXISTS (
                SELECT 1 FROM content c WHERE c.link_id = l.id
            )
        """, (page_id,))
        cur.execute("""
            UPDATE content
            SET status_id = (SELECT id FROM status WHERE name = 'pending')
            WHERE link_id IN (
                SELECT id FROM link WHERE page_id = %s
            )
            AND status_id != (SELECT id FROM status WHERE name = 'completed')
        """, (page_id,))
        conn.commit()
    finally:
        conn.close()
    