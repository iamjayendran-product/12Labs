from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.embeddings import embed_texts
from app.vectorstore import add_chunks, get_collection

CHUNKS = [
    {
        "id": "c1",
        "text": "Q: How is latency? A: Streaming responses take over a second, too slow for us.",
        "metadata": {
            "transcript_id": "call_test",
            "customer_name": "Test Customer",
            "company": "Test Co",
            "date": "2026-01-01",
        },
    },
]


@pytest.fixture
def populated_collection(tmp_path):
    collection = get_collection(db_dir=str(tmp_path))
    embeddings = embed_texts([c["text"] for c in CHUNKS])
    add_chunks(
        collection,
        ids=[c["id"] for c in CHUNKS],
        embeddings=embeddings,
        documents=[c["text"] for c in CHUNKS],
        metadatas=[c["metadata"] for c in CHUNKS],
    )
    return collection


@pytest.fixture
def client(monkeypatch, populated_collection):
    monkeypatch.setattr("app.rag.get_collection", lambda: populated_collection)
    from app.main import app as fastapi_app

    return TestClient(fastapi_app)


def test_chat_rejects_empty_question(client):
    response = client.post("/chat", json={"question": "   "})
    assert response.status_code == 400


def test_chat_returns_grounded_answer_via_ollama_by_default(client, monkeypatch):
    fake_response = SimpleNamespace(
        json=lambda: {"message": {"content": "Latency is a common complaint."}},
        raise_for_status=lambda: None,
    )
    monkeypatch.setattr("app.rag.httpx.post", lambda *a, **k: fake_response)

    response = client.post("/chat", json={"question": "How is latency?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Latency is a common complaint."
    assert body["sources"][0]["company"] == "Test Co"


def test_chat_omits_unrelated_sources_and_skips_generation(client, monkeypatch):
    def fail_if_called(*a, **k):
        raise AssertionError("generation backend should not be called when nothing is relevant")

    monkeypatch.setattr("app.rag.httpx.post", fail_if_called)

    response = client.post("/chat", json={"question": "Do you support Tamil language voices?"})

    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert "no feedback" in body["answer"].lower()


def test_chat_returns_500_when_ollama_unreachable(client, monkeypatch):
    def raise_connect_error(*a, **k):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.rag.httpx.post", raise_connect_error)

    response = client.post("/chat", json={"question": "How is latency?"})

    assert response.status_code == 500
    assert "Ollama" in response.json()["detail"]


def test_chat_returns_500_when_anthropic_api_key_missing(client, monkeypatch):
    monkeypatch.setenv("GENERATION_BACKEND", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.post("/chat", json={"question": "How is latency?"})

    assert response.status_code == 500
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_chat_returns_grounded_answer_via_anthropic_when_selected(client, monkeypatch):
    monkeypatch.setenv("GENERATION_BACKEND", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    fake_response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="Latency is a common complaint.")]
    )

    class FakeMessages:
        def create(self, **kwargs):
            return fake_response

    fake_client = SimpleNamespace(messages=FakeMessages())
    monkeypatch.setattr("app.rag._client", lambda: fake_client)

    response = client.post("/chat", json={"question": "How is latency?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Latency is a common complaint."
    assert body["sources"][0]["company"] == "Test Co"
