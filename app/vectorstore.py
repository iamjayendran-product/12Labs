"""Local persisted Chroma vector store wrapper."""
import os

import chromadb

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
COLLECTION_NAME = "feedback_chunks"


def get_collection(db_dir: str = DB_DIR):
    client = chromadb.PersistentClient(path=db_dir)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def reset_collection(db_dir: str = DB_DIR):
    client = chromadb.PersistentClient(path=db_dir)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return client.get_or_create_collection(name=COLLECTION_NAME)


def add_chunks(collection, ids, embeddings, documents, metadatas):
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(collection, embedding, top_k=5):
    return collection.query(query_embeddings=[embedding], n_results=top_k)
