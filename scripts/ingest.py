"""Reads data/transcripts/*.json, chunks each transcript, embeds the chunks
with a local model, and writes them into the local Chroma vector store.

Run: python scripts/ingest.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.embeddings import embed_texts
from app.vectorstore import add_chunks, reset_collection

TRANSCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "transcripts"
)


def chunk_transcript(transcript: dict) -> list[dict]:
    """One chunk per customer turn, paired with the preceding agent question
    for context. Each chunk carries transcript metadata for citation."""
    chunks = []
    turns = transcript["turns"]
    last_agent_text = None
    for i, turn in enumerate(turns):
        if turn["speaker"] == "agent":
            last_agent_text = turn["text"]
            continue
        question = last_agent_text or ""
        text = f"Q: {question}\nA: {turn['text']}" if question else turn["text"]
        chunks.append(
            {
                "id": f"{transcript['id']}_chunk{len(chunks)}",
                "text": text,
                "metadata": {
                    "transcript_id": transcript["id"],
                    "customer_name": transcript["customer_name"],
                    "company": transcript["company"],
                    "date": transcript["date"],
                },
            }
        )
    return chunks


def main():
    files = sorted(f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".json"))
    if not files:
        print(f"No transcripts found in {TRANSCRIPTS_DIR}")
        return

    all_chunks = []
    for fname in files:
        with open(os.path.join(TRANSCRIPTS_DIR, fname)) as f:
            transcript = json.load(f)
        all_chunks.extend(chunk_transcript(transcript))

    print(f"Loaded {len(files)} transcripts -> {len(all_chunks)} chunks. Embedding...")
    embeddings = embed_texts([c["text"] for c in all_chunks])

    collection = reset_collection()
    add_chunks(
        collection,
        ids=[c["id"] for c in all_chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in all_chunks],
        metadatas=[c["metadata"] for c in all_chunks],
    )

    print(f"Embedded and stored {len(all_chunks)} chunks in the vector store.")


if __name__ == "__main__":
    main()
