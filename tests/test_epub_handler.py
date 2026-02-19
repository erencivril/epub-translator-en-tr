from epub_handler import extract_text_nodes, replace_text_nodes


def test_extract_text_nodes_simple():
    html = "<html><body><h1>Hello World</h1><p>This is a test.</p></body></html>"
    nodes = extract_text_nodes(html)
    assert len(nodes) == 2
    assert nodes[0]["text"] == "Hello World"
    assert nodes[1]["text"] == "This is a test."


def test_extract_text_nodes_nested():
    html = "<html><body><p>Start <b>bold</b> end</p></body></html>"
    nodes = extract_text_nodes(html)
    texts = [n["text"] for n in nodes]
    assert "Start " in texts
    assert "bold" in texts
    assert " end" in texts


def test_extract_skips_empty():
    html = "<html><body><p>  </p><p>Real text</p></body></html>"
    nodes = extract_text_nodes(html)
    texts = [n["text"] for n in nodes]
    assert "Real text" in texts
    # Whitespace-only nodes should be skipped
    for t in texts:
        assert t.strip() != ""


def test_replace_text_nodes():
    html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
    nodes = extract_text_nodes(html)
    translations = {0: "Merhaba", 1: "Dünya"}
    result = replace_text_nodes(html, nodes, translations)
    assert "Merhaba" in result
    assert "Dünya" in result
    assert "<h1>" in result
    assert "<p>" in result
    assert "Hello" not in result
    assert "World" not in result


def test_extract_skips_script_and_style():
    html = (
        "<html><head><style>body { color: red; }</style></head>"
        "<body><script>var x = 1;</script><p>Real text</p></body></html>"
    )
    nodes = extract_text_nodes(html)
    texts = [n["text"] for n in nodes]
    assert texts == ["Real text"]


def test_extract_skips_html_comments():
    html = "<html><body><!-- copyright --><p>Real text</p></body></html>"
    nodes = extract_text_nodes(html)
    texts = [n["text"] for n in nodes]
    assert texts == ["Real text"]


def test_replace_preserves_structure():
    html = '<html><body><p class="intro">Start <b>bold</b> end</p></body></html>'
    nodes = extract_text_nodes(html)
    translations = {i: f"TR_{n['text']}" for i, n in enumerate(nodes)}
    result = replace_text_nodes(html, nodes, translations)
    assert '<p class="intro">' in result
    assert "<b>" in result
    assert "TR_Start " in result
    assert "TR_bold" in result
    assert "TR_ end" in result
