import chromadb
import os

try:
    path = "./content/.chroma_test"
    if not os.path.exists(path):
        os.makedirs(path)
    client = chromadb.PersistentClient(path=path)
    print("ChromaDB initialized successfully")
except Exception as e:
    print(f"ChromaDB failed: {e}")
