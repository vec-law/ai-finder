from db.connection import get_connection

def save_links(fetcher_id, links_dict: dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        for url, title in links_dict.items():
            cur.execute("""
                INSERT INTO link (url, title, fetcher_id, status_id)
                VALUES (
                    %s,
                    %s,
                    %s,
                    (SELECT id FROM status WHERE name = 'pending')    
                )
            """, (url, title, fetcher_id))
        conn.commit()
        
        return True
    
    finally:
        conn.close()

def get_pending_link_ids(fetcher_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT link.id FROM link
            JOIN fetcher ON fetcher.id = fetcher_id
            JOIN status ON status.id = status_id
            WHERE fetcher_id = %s
            AND status.name = 'pending'
        """, (fetcher_id, ))

        return [row[0] for row in cur.fetchall()]
    
    finally:
        conn.close()

def get_link_url(link_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT link.url FROM link
            WHERE link.id = %s
        """, (link_id, ))

        result = cur.fetchone()

        if not result:
            return None

        return result[0]
    
    finally:
        conn.close()

def update_link(link_id, content, embedding, status):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE link
            SET content = %s,
                embedding = %s,
                status_id = (SELECT id FROM status WHERE name = %s)
            WHERE id = %s
        """, (content, embedding, status, link_id))
        conn.commit()
        
        return True
    
    finally:
        conn.close()
