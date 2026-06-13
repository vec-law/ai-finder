from rag import RAG

rag = RAG()

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
