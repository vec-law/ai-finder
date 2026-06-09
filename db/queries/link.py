import os
from db.connection import get_connection
from dotenv import load_dotenv

load_dotenv()

def del_expired_links(config_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        expiry_days = int(os.getenv("LINK_EXPIRY_DAYS", 30))
        cur.execute("""
            DELETE FROM link
            WHERE fetcher_id IN (
                SELECT id FROM fetcher WHERE config_id = %s
            )
            AND created_at < NOW() - INTERVAL '%s days'
        """, (config_id, expiry_days))
        conn.commit()
    finally:
        conn.close()

def save_links(fetcher_id, links_dict: dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        for url, title in links_dict.items():
            cur.execute("""
                INSERT INTO link (url, title, fetcher_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (fetcher_id, url) DO NOTHING
            """, (url, title, fetcher_id))
            cur.execute("""
                SELECT id FROM link WHERE fetcher_id = %s AND url = %s
            """, (fetcher_id, url))
            link_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO content (link_id, status_id)
                VALUES (%s, (SELECT id FROM status WHERE name = 'pending'))
                ON CONFLICT (link_id) DO NOTHING
            """, (link_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_links(link_ids):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.id, l.title, l.url, c.content FROM link l
            JOIN content c ON c.link_id = l.id
            WHERE l.id IN %s
        """, (tuple(link_ids),))
        rows = {row[0]: {"id": row[0], "title": row[1], "url": row[2], "content": row[3]} for row in cur.fetchall()}
        return [rows[link_id] for link_id in link_ids if link_id in rows]
    finally:
        conn.close()
