import os
import re
from embeddings import get_embedding
from db.queries.search import search_links
from db.queries.link import get_links
from dotenv import load_dotenv

load_dotenv()

def test_search():
    all_good = count_good_in_db()
    total_good = len(all_good)
    model_name = os.getenv("EMBEDDING_MODEL", "unknown").replace("/", "_")
    os.makedirs("temp", exist_ok=True)

    while True:
        query = input("Zapytanie: ")
        if not query:
            continue
        if query == "exit":
            break
        
        embedding = get_embedding(query, is_query=True)
        link_ids = search_links(embedding)
        links = get_links(link_ids)

        query_slug = query[:30].replace(" ", "_").encode("ascii", "ignore").decode()
        filename = f"temp/{model_name}__{query_slug}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            for i, link in enumerate(links, 1):
                marker = "✓" if is_good(link['title'], link['content']) else " "
                f.write(f"{i}. [{marker}] {link['id']} {link['title']}\n")

        for threshold in range(100, 3001, 100):
            count = sum(1 for link in links[:threshold] if is_good(link['title'], link['content']))
            print(f"top {threshold}: {count}/{total_good}")

        print(f"\nZapisano: {filename}")

def count_good_in_db():
    from db.connection import get_connection
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.id, l.title, c.content FROM link l
            JOIN content c ON c.link_id = l.id
            WHERE c.status_id = (SELECT id FROM status WHERE name = 'completed')
        """)
        rows = cur.fetchall()
        good = [{'id': row[0], 'title': row[1], 'content': row[2]} for row in rows if is_good(row[1], row[2])]
        print(f"Dobre oferty w bazie: {len(good)}/{len(rows)}")
        return good
    finally:
        conn.close()

def is_good(title, content):
    t_title = title.lower()
    t_content = content.lower()
    t_both = t_title + " " + t_content
    bad = ['senior', 'starszy', 'starsza', 'lead', 'kierownik', 'kierowniczka', 'architect', 'architekt', 'principal', 'staff', 'head', 'director', 'manager', 'mid-level', 'middle']
    junior = ['junior', 'młodszy', 'młodsza', 'praktykant', 'staż', 'stażysta']
    
    if any(re.search(r'\b' + b + r'\b', t_title) for b in bad):
        return False
    if not re.search(r'\bpython\b', t_both):
        return False
    return any(re.search(r'\b' + j + r'\b', t_both) for j in junior)
