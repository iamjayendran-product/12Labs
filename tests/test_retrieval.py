from app.embeddings import embed_query, embed_texts
from app.vectorstore import add_chunks, get_collection, query

CHUNKS = [
    {
        "id": "c1",
        "text": "Q: How is response latency? A: The streaming API is too slow, over a second of delay.",
        "metadata": {"topic": "latency"},
    },
    {
        "id": "c2",
        "text": "Q: How is pricing? A: The character-based pricing gets expensive at scale.",
        "metadata": {"topic": "pricing"},
    },
    {
        "id": "c3",
        "text": "Q: How is support? A: Support resolved our ticket within a few hours, great experience.",
        "metadata": {"topic": "support"},
    },
]


def populate(db_dir):
    collection = get_collection(db_dir=str(db_dir))
    embeddings = embed_texts([c["text"] for c in CHUNKS])
    add_chunks(
        collection,
        ids=[c["id"] for c in CHUNKS],
        embeddings=embeddings,
        documents=[c["text"] for c in CHUNKS],
        metadatas=[c["metadata"] for c in CHUNKS],
    )
    return collection


def test_query_retrieves_topically_relevant_chunk_first(tmp_path):
    collection = populate(tmp_path)

    embedding = embed_query("Is the API slow to respond?")
    results = query(collection, embedding, top_k=1)

    assert results["ids"][0][0] == "c1"


def test_query_distinguishes_pricing_from_latency(tmp_path):
    collection = populate(tmp_path)

    embedding = embed_query("Is it too costly to use at scale?")
    results = query(collection, embedding, top_k=1)

    assert results["ids"][0][0] == "c2"


def test_query_returns_metadata_alongside_documents(tmp_path):
    collection = populate(tmp_path)

    embedding = embed_query("How responsive is customer support?")
    results = query(collection, embedding, top_k=1)

    assert results["metadatas"][0][0]["topic"] == "support"
