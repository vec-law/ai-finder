import os
from db.connection import get_connection
from dotenv import load_dotenv

load_dotenv()

def set_links_pending():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE link
            SET status_id = (SELECT id FROM status WHERE name = 'pending')
            WHERE status_id IN (
                SELECT id FROM status WHERE name IN ('running', 'failed')
            )
        """)
        conn.commit()
        
        return True
    
    finally:
        conn.close()

def get_links(link_ids):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, content FROM link
            WHERE id IN %s
        """, (tuple(link_ids), ))

        return [
            {
                "id": row[0],
                "title": row[1],
                "content": row[2]
            } for row in cur.fetchall()
        ]
    
    finally:
        conn.close()  

def search_links(embedding, limit=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        if limit:
            cur.execute("""
                SELECT id FROM link
                WHERE status_id = (SELECT id FROM status WHERE name = 'completed')
                ORDER BY embedding <=> %s
                LIMIT %s
            """, (embedding, limit))
        else:
            cur.execute("""
            SELECT id FROM link
            WHERE status_id = (SELECT id FROM status WHERE name = 'completed')
            ORDER BY embedding <=> %s
            """, (embedding,))

        return [row[0] for row in cur.fetchall()]
    
    finally:
        conn.close()

def save_links(fetcher_id, links_dict: dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        expiry_days = int(os.getenv("LINK_EXPIRY_DAYS", 30))

        for url, title in links_dict.items():
            cur.execute("""
                INSERT INTO link (url, title, fetcher_id, status_id)
                VALUES (
                    %s,
                    %s,
                    %s,
                    (SELECT id FROM status WHERE name = 'pending')    
                )
                ON CONFLICT (fetcher_id, url) DO UPDATE
                SET status_id = (SELECT id FROM status WHERE name = 'pending'),
                    created_at = NOW()
                WHERE link.status_id != (SELECT id FROM status WHERE name = 'completed')
                OR link.created_at < NOW() - INTERVAL '%s days'
            """, (url, title, fetcher_id, expiry_days))
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
            JOIN fetcher ON fetcher.id = link.fetcher_id
            JOIN status ON status.id = link.status_id
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
