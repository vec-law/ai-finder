from rag import RAG

rag = RAG()

while True:
    query = input("Zapytanie: ").strip()
    if not query:
        continue
    if query.lower() == "exit":
        break
    response = rag.run(query)
    print(f"\n{response}\n")
