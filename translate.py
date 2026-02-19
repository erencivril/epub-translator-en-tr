#!/usr/bin/env python3
# translate.py
"""EPUB Translator - Translates EPUB files from English to Turkish using AI."""

import argparse
import os
import sys

from dotenv import load_dotenv
from ebooklib import epub

from epub_handler import (
    extract_text_nodes,
    get_chapters,
    read_epub,
    replace_text_nodes,
    save_epub,
)
from progress import ProgressTracker
from translator import DEFAULT_MODEL, translate_nodes


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="EPUB dosyalarını İngilizce'den Türkçe'ye çevirir."
    )
    parser.add_argument("input", help="Çevrilecek EPUB dosyasının yolu")
    parser.add_argument("-o", "--output", help="Çıktı EPUB dosyasının yolu")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"OpenRouter model (varsayılan: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Kaldığı yerden devam et"
    )

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input):
        print(f"Hata: '{args.input}' dosyası bulunamadı.")
        sys.exit(1)

    # API key check
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("Hata: OPENROUTER_API_KEY ayarlanmamış.")
        print("  .env dosyasına OPENROUTER_API_KEY=sk-or-... ekleyin")
        print("  veya: export OPENROUTER_API_KEY=sk-or-...")
        sys.exit(1)

    # Output path
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        output_path = f"{base}_tr{ext}"

    # Progress file
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    progress_path = os.path.join(os.path.dirname(args.input) or ".", f"{base_name}.progress.json")

    print(f"Kaynak: {args.input}")
    print(f"Çıktı:  {output_path}")
    print(f"Model:  {args.model}")
    print()

    # Read EPUB
    print("EPUB okunuyor...")
    book = read_epub(args.input)

    # Fix missing uid on TOC Link items (known ebooklib issue)
    for i, item in enumerate(book.toc):
        if isinstance(item, epub.Link) and item.uid is None:
            item.uid = f"toc_{i}"

    chapters = get_chapters(book)

    if not chapters:
        print("Hata: EPUB'da çevrilecek bölüm bulunamadı.")
        sys.exit(1)

    print(f"{len(chapters)} bölüm bulundu.\n")

    # Setup progress tracker
    if args.resume and os.path.exists(progress_path):
        tracker = ProgressTracker.load(progress_path)
        skipped = len(tracker.completed)
        print(f"Kaldığı yerden devam ediliyor ({skipped} bölüm tamamlanmış).\n")
    else:
        tracker = ProgressTracker(
            progress_path, total=len(chapters), source=args.input, model=args.model
        )

    # Translate each chapter
    for i, chapter in enumerate(chapters):
        chapter_name = chapter.get_name()

        if tracker.is_completed(chapter_name):
            continue

        tracker.print_progress(chapter_name)

        html = chapter.get_content().decode("utf-8")
        nodes = extract_text_nodes(html)

        if not nodes:
            tracker.mark_completed(chapter_name)
            continue

        try:
            translations = translate_nodes(
                nodes,
                model=args.model,
                api_key=api_key,
            )

            new_html = replace_text_nodes(html, nodes, translations)
            chapter.set_content(new_html.encode("utf-8"))
            tracker.mark_completed(chapter_name)

        except Exception as e:
            print(f"\nHata ({chapter_name}): {e}")
            tracker.mark_failed(chapter_name)
            continue

    print()
    print()

    # Save translated EPUB
    print(f"EPUB kaydediliyor: {output_path}")
    save_epub(book, output_path)

    # Report
    done = len(tracker.completed)
    failed = len(tracker.failed)
    print(f"\nTamamlandı! {done}/{len(chapters)} bölüm çevrildi.", end="")
    if failed:
        print(f" ({failed} bölüm başarısız)")
    else:
        print()

    # Clean up progress file on full success
    if failed == 0 and os.path.exists(progress_path):
        os.remove(progress_path)
        print("İlerleme dosyası temizlendi.")


if __name__ == "__main__":
    main()
