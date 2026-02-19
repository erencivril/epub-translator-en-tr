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
    response = "[1] Merhaba Dünya\n[2] Bu bir test."
    result = parse_response(response, count=2)
    assert result[0] == "Merhaba Dünya"
    assert result[1] == "Bu bir test."


def test_parse_response_multiline():
    response = "[1] Birinci satır\ndevam ediyor\n[2] İkinci öğe"
    result = parse_response(response, count=2)
    assert result[0] == "Birinci satır\ndevam ediyor"
    assert result[1] == "İkinci öğe"
