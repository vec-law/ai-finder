from db.connection import get_connection

def search_links(embedding, limit=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        embedding_str = "[" + ",".join(map(str, embedding.tolist())) + "]"
        if limit:
            cur.execute("""
                SELECT l.id FROM link l
                JOIN content c ON c.link_id = l.id
                JOIN embedding e ON e.content_id = c.id
                WHERE e.status_id = (SELECT id FROM status WHERE name = 'completed')
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
            """, (embedding_str, limit))
        else:
            cur.execute("""
                SELECT l.id FROM link l
                JOIN content c ON c.link_id = l.id
                JOIN embedding e ON e.content_id = c.id
                WHERE e.status_id = (SELECT id FROM status WHERE name = 'completed')
                ORDER BY e.embedding <=> %s::vector
            """, (embedding_str,))
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
