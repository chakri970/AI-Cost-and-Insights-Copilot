from api.app.rag import retriever

results = retriever.query("Show me cost by owner for April", top_k=5)
for r in results:
    print(r)
