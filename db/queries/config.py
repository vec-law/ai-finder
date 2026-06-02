from db.connection import get_connection

def get_saved_config():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT hash
            FROM config
            ORDER BY created_at DESC
            LIMIT 1
        """)
        result = cur.fetchone()

        return result[0] if result else None 
    
    finally:
        conn.close()

def save_config(config_hash):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO config (hash)
            VALUES (%s)
        """, (config_hash, ))
        conn.commit()
        
        return True
    
    finally:
        conn.close()

def del_old_configs():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM config
        """,)
        conn.commit()
        
        return True
    
    finally:
        conn.close()
