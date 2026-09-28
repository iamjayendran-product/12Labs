from scripts.ingest import chunk_transcript


def make_transcript(turns):
    return {
        "id": "call_test",
        "customer_name": "Test Customer",
        "company": "Test Co",
        "date": "2026-01-01",
        "turns": turns,
    }


def test_chunk_transcript_pairs_each_customer_turn_with_preceding_question():
    transcript = make_transcript(
        [
            {"speaker": "agent", "text": "How is voice quality?"},
            {"speaker": "customer", "text": "It's great."},
            {"speaker": "agent", "text": "Any issues?"},
            {"speaker": "customer", "text": "Latency is high."},
        ]
    )

    chunks = chunk_transcript(transcript)

    assert len(chunks) == 2
    assert chunks[0]["text"] == "Q: How is voice quality?\nA: It's great."
    assert chunks[1]["text"] == "Q: Any issues?\nA: Latency is high."


def test_chunk_transcript_attaches_metadata_for_citation():
    transcript = make_transcript(
        [
            {"speaker": "agent", "text": "How is pricing?"},
            {"speaker": "customer", "text": "Too expensive."},
        ]
    )

    chunks = chunk_transcript(transcript)

    assert chunks[0]["metadata"] == {
        "transcript_id": "call_test",
        "customer_name": "Test Customer",
        "company": "Test Co",
        "date": "2026-01-01",
    }


def test_chunk_transcript_ids_are_unique_and_ordered():
    transcript = make_transcript(
        [
            {"speaker": "agent", "text": "Q1"},
            {"speaker": "customer", "text": "A1"},
            {"speaker": "customer", "text": "A2 (no preceding question this time)"},
        ]
    )

    chunks = chunk_transcript(transcript)

    assert [c["id"] for c in chunks] == ["call_test_chunk0", "call_test_chunk1"]


def test_chunk_transcript_handles_customer_turn_with_no_preceding_agent_turn():
    transcript = make_transcript([{"speaker": "customer", "text": "Unprompted feedback."}])

    chunks = chunk_transcript(transcript)

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Unprompted feedback."


def test_chunk_transcript_empty_turns_produces_no_chunks():
    transcript = make_transcript([])

    assert chunk_transcript(transcript) == []
