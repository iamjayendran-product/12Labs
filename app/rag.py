"""Retrieval-augmented answer generation over the customer feedback corpus."""
import os

import httpx
from anthropic import Anthropic

from app.embeddings import embed_query
from app.vectorstore import get_collection, query

ANTHROPIC_MODEL = "claude-sonnet-5"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_K_M")
TOP_K = 5

# Chroma's default distance space is squared L2 over the raw sentence-transformers
# embeddings (not cosine). Empirically, on-topic matches score well under 1.0 and
# off-topic ones score well above it — see tests/test_retrieval.py. Chunks scoring
# above this are treated as "not actually relevant" rather than passed to the model,
# so the sources list only ever reflects what the answer could plausibly be grounded in.
RELEVANCE_THRESHOLD = 1.0

SYSTEM_PROMPT = """You are the 12Labs feedback assistant. You answer questions about \
customer/client feedback using ONLY the transcript excerpts provided in context.

Rules:
- Answer strictly from the provided excerpts. Do not use outside knowledge and do not guess.
- When you make a claim, attribute it to the customer/company it came from.
- If none of the provided excerpts are relevant to the question, say plainly that there is \
no feedback on that topic in the collated data. Do not fabricate an answer.
- Be concise and direct."""


def _client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set (check your .env file)")
    return Anthropic(api_key=api_key)


def _generate_anthropic(user_message: str) -> str:
    client = _client()
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _generate_ollama(user_message: str) -> str:
    try:
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Could not reach local Ollama server at {OLLAMA_URL}. "
            "Run `brew services start ollama` (or `ollama serve`) first."
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Ollama returned an error ({e.response.status_code}). "
            f"Is the model pulled? Try: ollama pull {OLLAMA_MODEL}"
        )
    return response.json()["message"]["content"]


def _generate(user_message: str) -> str:
    backend = os.environ.get("GENERATION_BACKEND", "ollama")
    if backend == "anthropic":
        return _generate_anthropic(user_message)
    return _generate_ollama(user_message)


def answer_question(question: str) -> dict:
    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError("Vector store is empty. Run scripts/ingest.py first.")

    query_embedding = embed_query(question)
    results = query(collection, query_embedding, top_k=TOP_K)

    all_documents = results["documents"][0]
    all_metadatas = results["metadatas"][0]
    all_distances = results["distances"][0]

    documents = []
    metadatas = []
    for doc, meta, dist in zip(all_documents, all_metadatas, all_distances):
        if dist <= RELEVANCE_THRESHOLD:
            documents.append(doc)
            metadatas.append(meta)

    if not documents:
        return {
            "answer": "There is no feedback on that topic in the collated data.",
            "sources": [],
        }

    context_blocks = []
    for doc, meta in zip(documents, metadatas):
        context_blocks.append(
            f"[Source: {meta['customer_name']}, {meta['company']}, {meta['date']}]\n{doc}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    user_message = (
        f"Customer feedback excerpts:\n\n{context}\n\n---\n\nQuestion: {question}"
    )

    answer_text = _generate(user_message)

    sources = [
        {
            "transcript_id": meta["transcript_id"],
            "customer_name": meta["customer_name"],
            "company": meta["company"],
            "date": meta["date"],
        }
        for meta in metadatas
    ]

    return {"answer": answer_text, "sources": sources}
