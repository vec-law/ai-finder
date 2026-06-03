from db.connection import get_connection

def save_links(config_hash, links_dict: dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        for url, title in links_dict.items():
            cur.execute("""
                INSERT INTO link (url, title, config_id, status_id)
                VALUES (
                    %s,
                    %s,
                    (SELECT id from config WHERE hash = %s),
                    (SELECT id FROM status WHERE name = 'pending')    
                )
            """, (url, title, config_hash))
        conn.commit()
        
        return True
    
    finally:
        conn.close()

def get_pending_link_ids(config_hash):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM link
            JOIN config ON config.id = config_id
            JOIN status ON status.id = status_id
            WHERE config.hash = %s
            AND status.name = 'pending'
        """, (config_hash, ))

        return [row[0] for row in cur.fetchall()]
    
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
