"""Creates a minimal test EPUB for integration testing."""
from ebooklib import epub


def create_test_epub(filepath: str):
    book = epub.EpubBook()
    book.set_identifier("test-book-001")
    book.set_title("Test Book")
    book.set_language("en")
    book.add_author("Test Author")

    # Chapter 1
    ch1 = epub.EpubHtml(title="Chapter 1", file_name="ch1.xhtml", lang="en")
    ch1.content = b"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
<h1>Chapter One: The Beginning</h1>
<p>It was a dark and stormy night. The wind howled through the trees.</p>
<p>She looked out the window and <b>sighed deeply</b>.</p>
</body>
</html>"""

    # Chapter 2
    ch2 = epub.EpubHtml(title="Chapter 2", file_name="ch2.xhtml", lang="en")
    ch2.content = b"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 2</title></head>
<body>
<h1>Chapter Two: The Journey</h1>
<p>The next morning brought sunshine and hope.</p>
<ul>
<li>Pack the bags</li>
<li>Say goodbye</li>
<li>Hit the road</li>
</ul>
</body>
</html>"""

    book.add_item(ch1)
    book.add_item(ch2)

    book.toc = [
        epub.Link("ch1.xhtml", "Chapter 1", "ch1"),
        epub.Link("ch2.xhtml", "Chapter 2", "ch2"),
    ]

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", ch1, ch2]

    epub.write_epub(filepath, book)
    return filepath


if __name__ == "__main__":
    create_test_epub("tests/test_book.epub")
    print("Test EPUB created: tests/test_book.epub")
