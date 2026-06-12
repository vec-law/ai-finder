from db.connection import get_connection

def get_or_create_fetcher(name):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fetcher (name) VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
        """, (name,))
        row = cur.fetchone()
        if row:
            conn.commit()
            return row[0]
        conn.rollback()
        cur.execute("SELECT id FROM fetcher WHERE name = %s", (name,))
        return cur.fetchone()[0]
    finally:
        conn.close()
