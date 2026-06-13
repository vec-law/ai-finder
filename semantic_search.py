from embedder import Embedder
from db.queries.search import search_links as db_search_links
from db.queries.link import get_links as db_get_links

embedder = Embedder()

while True:
    query = input("\nZapytanie: ").strip()
    if not query:
        continue
    if query.lower() == "exit":
        break
    
    embedding = embedder.get_embedding(query, type="query")
    link_ids = db_search_links(embedding, limit=200)
    results = db_get_links(link_ids)

    if not results:
        continue

    print("\nWyniki wyszukiwania:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}: {result['title']}\nurl: {result['url']}")
