import httpx

import translator
from translator import chunk_text_nodes, format_chunk, parse_response


def test_chunk_text_nodes_single():
    nodes = [{"index": 0, "text": "Hello"}, {"index": 1, "text": "World"}]
    chunks = chunk_text_nodes(nodes, max_tokens=1000)
    assert len(chunks) == 1
    assert len(chunks[0]) == 2


def test_chunk_text_nodes_splits():
    # Create nodes that exceed token limit
    nodes = [{"index": i, "text": f"Word{i} " * 100} for i in range(20)]
    chunks = chunk_text_nodes(nodes, max_tokens=500)
    assert len(chunks) > 1
    # All nodes should be present across chunks
    all_indices = [n["index"] for chunk in chunks for n in chunk]
    assert all_indices == list(range(20))


def test_format_chunk():
    nodes = [
        {"index": 0, "text": "Hello World"},
        {"index": 1, "text": "This is a test."},
    ]
    result = format_chunk(nodes)
    assert "[1] Hello World" in result
    assert "[2] This is a test." in result


def test_parse_response_simple():
    response = "[1] Hello World\n[2] This is a test."
    result = parse_response(response, count=2)
    assert result[0] == "Hello World"
    assert result[1] == "This is a test."


def test_parse_response_multiline():
    response = "[1] First line\ncontinues here\n[2] Second item"
    result = parse_response(response, count=2)
    assert result[0] == "First line\ncontinues here"
    assert result[1] == "Second item"


def test_translate_chunk_retries_after_429_then_succeeds(monkeypatch):
    calls = {"count": 0}
    sleeps = []

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        request = httpx.Request("POST", translator.OPENROUTER_URL)
        if calls["count"] == 1:
            return httpx.Response(
                429,
                request=request,
                headers={"Retry-After": "1"},
                json={"error": {"message": "rate limited"}},
            )
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"content": "[1] Merhaba"}}]},
        )

    monkeypatch.setattr(translator.httpx, "post", fake_post)
    monkeypatch.setattr(translator.time, "sleep", lambda s: sleeps.append(s))

    result = translator.translate_chunk([{"index": 0, "text": "Hello"}], api_key="test-key")
    assert result[0] == "Merhaba"
    assert calls["count"] == 2
    assert sleeps == [1.0]


def test_translate_chunk_retries_after_request_error_then_succeeds(monkeypatch):
    calls = {"count": 0}
    sleeps = []

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            request = httpx.Request("POST", translator.OPENROUTER_URL)
            raise httpx.ReadTimeout("timeout", request=request)
        request = httpx.Request("POST", translator.OPENROUTER_URL)
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"content": "[1] Selam"}}]},
        )

    monkeypatch.setattr(translator.httpx, "post", fake_post)
    monkeypatch.setattr(translator.random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(translator.time, "sleep", lambda s: sleeps.append(s))

    result = translator.translate_chunk([{"index": 0, "text": "Hello"}], api_key="test-key")
    assert result[0] == "Selam"
    assert calls["count"] == 2
    assert sleeps == [1.0]


def test_translate_chunk_raises_after_max_retries(monkeypatch):
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        request = httpx.Request("POST", translator.OPENROUTER_URL)
        return httpx.Response(
            503,
            request=request,
            json={"error": {"message": "temporary unavailable"}},
        )

    monkeypatch.setattr(translator.httpx, "post", fake_post)
    monkeypatch.setattr(translator.time, "sleep", lambda s: None)

    try:
        translator.translate_chunk([{"index": 0, "text": "Hello"}], api_key="test-key")
        assert False, "Expected HTTPStatusError"
    except httpx.HTTPStatusError:
        pass

    assert calls["count"] == translator.MAX_API_ATTEMPTS
