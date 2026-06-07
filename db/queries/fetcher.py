from db.connection import get_connection

def save_fetcher(config_id, url):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM fetcher
            WHERE config_id = %s
            AND url = %s
        """, (config_id, url))

        result = cur.fetchone()
        if result:
            return result[0]

        cur.execute("""
            INSERT INTO fetcher (config_id, url)
            VALUES (%s, %s)
            RETURNING id
        """, (config_id, url))
        conn.commit()

        return cur.fetchone()[0]
    
    finally:
        conn.close()
