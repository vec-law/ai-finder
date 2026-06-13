import os
from db.connection import get_connection
from dotenv import load_dotenv

load_dotenv()

def save_links(page_id, links_dict: dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        for url, title in links_dict.items():
            cur.execute("""
                INSERT INTO link (url, title, page_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (page_id, url) DO NOTHING
            """, (url, title, page_id))
            conn.commit()
        return True
    finally:
        conn.close()

def del_expired_links(page_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        expiry_days = int(os.getenv("LINK_EXPIRY_DAYS", 30))
        cur.execute("""
            DELETE FROM link
            WHERE page_id = %s
            AND created_at < NOW() - INTERVAL '1 day' * %s
        """, (page_id, expiry_days))
        conn.commit()
    finally:
        conn.close()

def get_links(link_ids):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.url, l.title, c.content FROM link l
            JOIN content c ON c.link_id = l.id
            WHERE l.id = ANY(%s)
        """, (link_ids,))
        return [{"url": row[0], "title": row[1], "content": row[2]} for row in cur.fetchall()]
    finally:
        conn.close()
