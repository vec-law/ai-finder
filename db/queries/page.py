from db.connection import get_connection

def update_domain(page_id, domain):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE page SET domain = %s WHERE id = %s", (domain, page_id))
        conn.commit()
    finally:
        conn.close()

def get_domain(url):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT domain FROM page WHERE url = %s LIMIT 1", (url,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def get_or_create_page(url, page_type, page_max, fetcher_id, embedding_model_name, embedding_vector_size):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO page (url, page_type_id, page_max, fetcher_id, embedding_model_name, embedding_vector_size)
            VALUES (
                %s,
                (SELECT id FROM page_type WHERE name = %s),
                %s,
                %s,
                %s,
                %s
            )
            ON CONFLICT (url, page_type_id, page_max, fetcher_id) DO NOTHING
            RETURNING id
        """, (url, page_type, page_max, fetcher_id, embedding_model_name, embedding_vector_size))
        row = cur.fetchone()
        if row:
            conn.commit()
            return row[0]
        conn.rollback()
        cur.execute("""
            SELECT p.id FROM page p
            JOIN page_type pt ON pt.id = p.page_type_id
            WHERE p.url = %s AND pt.name = %s AND p.page_max = %s AND p.fetcher_id = %s
        """, (url, page_type, page_max, fetcher_id))
        return cur.fetchone()[0]
    finally:
        conn.close()

def update_embedding_config(page_id, embedding_model_name, embedding_vector_size):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT embedding_model_name, embedding_vector_size FROM page WHERE id = %s
        """, (page_id,))
        row = cur.fetchone()
        db_model, db_vector_size = row[0], row[1]
        if db_model == embedding_model_name and db_vector_size == embedding_vector_size:
            return embedding_model_name, embedding_vector_size
        cur.execute("""
            DELETE FROM embedding
            WHERE content_id IN (
                SELECT c.id FROM content c
                JOIN link l ON l.id = c.link_id
                WHERE l.page_id = %s
            )
        """, (page_id,))
        conn.commit()

        conn.autocommit = True
        cur.execute(f"ALTER TABLE embedding ALTER COLUMN embedding TYPE VECTOR({embedding_vector_size})")
        conn.autocommit = False

        cur.execute("""
            UPDATE page SET embedding_model_name = %s, embedding_vector_size = %s WHERE id = %s
        """, (embedding_model_name, embedding_vector_size, page_id))
        conn.commit()
        return embedding_model_name, embedding_vector_size
    finally:
        conn.close()
