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
