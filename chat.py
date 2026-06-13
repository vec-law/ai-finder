from rag import RAG

rag = RAG()

if not rag.domain:
    print("Uwaga: baza nie zawiera jeszcze zaindeksowanych danych. Uruchom najpierw run_indexer.py.")

while True:
    query = input("Zapytanie: ").strip()
    if not query:
        continue
    if query.lower() == "exit":
        break
    
    response = rag.run(query)
    if response is None:
        print("\nBłąd: nie udało się uzyskać odpowiedzi.\n")
    else:
        print(f"\n{response}\n")
