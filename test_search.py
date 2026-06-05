from embeddings import get_embedding
from db.queries.link import search_links, get_links

def test_search():
    while True:
        query = input("Zapytanie: ")
        if not query:
            continue
        if query == "exit":
            break
        
        embedding = get_embedding(query)
        link_ids = search_links(embedding, limit=1000)
        links = get_links(link_ids)
        
        for i, link in enumerate(links, 1):
            print(f"{i}. {link['title']}")
        print("---")

        # po pętli for:
        good_count = sum(1 for link in links if is_good(link['title']))
        print(f"Trafione: {good_count}/{len(links)}")

def is_good(title):
    t = title.lower()
    bad = ['senior', 'starszy', 'starsza', 'lead', 'kierownik', 'kierowniczka', 'architect', 'architekt', 'principal', 'staff', 'head', 'director', 'manager', 'mid-level', 'middle']
    good = ['python', 'junior', 'młodszy', 'młodsza', 'praktykant', 'staż', 'stażysta']
    if any(b in t for b in bad):
        return False
    return any(g in t for g in good)

