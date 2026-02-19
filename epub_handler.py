# epub_handler.py
import warnings

from bs4 import BeautifulSoup, NavigableString, Comment, CData, ProcessingInstruction, XMLParsedAsHTMLWarning
import ebooklib
from ebooklib import epub

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

_SKIP_NS_TYPES = (Comment, CData, ProcessingInstruction)


def extract_text_nodes(html: str) -> list[dict]:
    """Extract all meaningful text nodes from HTML, preserving order."""
    soup = BeautifulSoup(html, "lxml")
    nodes = []

    for element in soup.descendants:
        if isinstance(element, _SKIP_NS_TYPES):
            continue
        if isinstance(element, NavigableString):
            if element.parent and element.parent.name in ("script", "style"):
                continue
            text = str(element)
            if not text.strip():
                continue
            nodes.append({
                "index": len(nodes),
                "text": text,
            })

    return nodes


def replace_text_nodes(html: str, nodes: list[dict], translations: dict[int, str]) -> str:
    """Replace text nodes in HTML with translations. translations maps node index to translated text."""
    soup = BeautifulSoup(html, "lxml")

    text_node_idx = 0
    for element in list(soup.descendants):
        if isinstance(element, _SKIP_NS_TYPES):
            continue
        if isinstance(element, NavigableString):
            if element.parent and element.parent.name in ("script", "style"):
                continue
            text = str(element)
            if not text.strip():
                continue
            if text_node_idx in translations:
                element.replace_with(NavigableString(translations[text_node_idx]))
            text_node_idx += 1

    return str(soup)


def read_epub(filepath: str) -> epub.EpubBook:
    """Read an EPUB file and return the book object."""
    return epub.read_epub(filepath)


def get_chapters(book: epub.EpubBook) -> list[epub.EpubItem]:
    """Get all document chapters from the EPUB book."""
    chapters = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item)
    return chapters


def save_epub(book: epub.EpubBook, filepath: str):
    """Save the EPUB book to a file."""
    epub.write_epub(filepath, book)
