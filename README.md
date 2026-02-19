# EPUB Translator (English -> Turkish)

A command-line tool that translates EPUB e-books from English to Turkish through the OpenRouter API while preserving the original book structure and formatting.

## Features

- Format preservation: keeps HTML structure, CSS, images, headings, and lists intact.
- Whitespace preservation: protects spacing around inline tags like `<b>` and `<i>`.
- Progress tracking: live progress bar with percentage and ETA.
- Checkpoint/resume: continues interrupted runs with `--resume`.
- Uncensored translation behavior: translator prompt is configured to preserve source meaning without censorship.
- Cost/performance profile: with Gemini Flash models, a typical novel can be low cost (often around `$0.05-$0.10`, depending on model and content).

## Requirements

- Python 3.10+
- OpenRouter API key

## Installation

```bash
git clone https://github.com/erencivril/epub-translator-en-tr.git
cd epub-translator-en-tr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set your API key in `.env`:

```env
OPENROUTER_API_KEY=sk-or-...
```

## Usage

```bash
source venv/bin/activate

# Basic usage
python translate.py book.epub

# Custom output file
python translate.py book.epub -o translated.epub

# Use a different model
python translate.py book.epub --model google/gemini-2.5-flash

# Resume after interruption
python translate.py book.epub --resume
```

## How It Works

1. Loads the EPUB with `ebooklib`.
2. Extracts translatable text nodes from chapter HTML using BeautifulSoup.
3. Splits text nodes into token-safe chunks.
4. Sends chunks to OpenRouter Chat Completions.
5. Writes translated text back into the same HTML structure.
6. Saves a translated EPUB file.

## Output and Progress Files

- Default output file: `<input_name>_tr.epub`
- Checkpoint file: `<input_name>.progress.json`
- The checkpoint file is removed automatically when all chapters succeed.

## Testing

```bash
source venv/bin/activate
python -m pytest -v
```

## Security Notes

- `.env` and `.env.*` are gitignored by default.
- Local EPUB files are gitignored by default (`*.epub`), except tracked test fixtures under `tests/`.
