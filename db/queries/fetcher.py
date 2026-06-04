from db.connection import get_connection

def save_fetcher(config_hash, url):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM fetcher
            WHERE config_id = (SELECT id FROM config WHERE hash = %s)
            AND url = %s
        """, (config_hash, url))

        result = cur.fetchone()
        if result:
            return result[0]

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