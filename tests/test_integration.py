import os
import tempfile

from ebooklib import epub
from tests.create_test_epub import create_test_epub
from epub_handler import read_epub, get_chapters, extract_text_nodes, replace_text_nodes, save_epub


def _fix_toc_uids(book: epub.EpubBook):
    """Fix missing uid on TOC Link items after read_epub (known ebooklib issue)."""
    for i, item in enumerate(book.toc):
        if isinstance(item, epub.Link) and item.uid is None:
            item.uid = f"toc_{i}"


def test_full_pipeline_without_api():
    """Test the full pipeline: read EPUB -> extract -> mock translate -> replace -> save."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test EPUB
        input_path = os.path.join(tmpdir, "test.epub")
        create_test_epub(input_path)

        # Read (3 documents: ch1, ch2, and the nav page)
        book = read_epub(input_path)
        _fix_toc_uids(book)
        chapters = get_chapters(book)
        assert len(chapters) == 3

        # Process each chapter
        for chapter in chapters:
            html = chapter.get_content().decode("utf-8")
            nodes = extract_text_nodes(html)
            assert len(nodes) > 0

            # Mock translation: prepend TR_ to each node
            translations = {n["index"]: f"TR_{n['text']}" for n in nodes}
            new_html = replace_text_nodes(html, nodes, translations)

            # Verify structure preserved and translations applied
            assert "TR_" in new_html

            chapter.set_content(new_html.encode("utf-8"))

        # Save
        output_path = os.path.join(tmpdir, "test_tr.epub")
        save_epub(book, output_path)
        assert os.path.exists(output_path)

        # Verify output EPUB is readable
        out_book = read_epub(output_path)
        out_chapters = get_chapters(out_book)
        assert len(out_chapters) == 3
