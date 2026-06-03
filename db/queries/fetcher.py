from db.connection import get_connection

def save_fetcher(config_hash, url):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fetcher (config_id, url)
            VALUES (
                (SELECT id FROM config WHERE hash = %s),
                %s
            )
            RETURNING id
        """, (config_hash, url))
        conn.commit()

        result = cur.fetchone()

        if not result:
            return None
        
        return result[0]
    
    finally:
        conn.close()