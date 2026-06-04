from embeddings import get_embedding
from db.queries.link import search_links, get_links

def test_search():
    while True:
        query = input("Zapytanie: ")
        if not query:
            continue
        
        embedding = get_embedding(query)
        link_ids = search_links(embedding, limit=100)
        links = get_links(link_ids)
        
        for i, link in enumerate(links, 1):
            print(f"{i}. {link['title']}")
        print("---")
