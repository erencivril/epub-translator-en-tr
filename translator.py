"""Translator module: OpenRouter API client with text chunking for EPUB translation."""

import os
import random
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.0-flash-001"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_API_ATTEMPTS = 5
BASE_RETRY_DELAY_SECONDS = 1.0
MAX_RETRY_DELAY_SECONDS = 16.0
RETRY_JITTER_SECONDS = 0.25

SYSTEM_PROMPT = """Sen profesyonel bir İngilizce-Türkçe kitap çevirmenisin.

Kurallar:
- Edebi, akıcı, doğal Türkçe üret
- Sansür yapma, orijinal metni olduğu gibi çevir
- Sadece çeviriyi döndür, açıklama veya yorum ekleme
- Numaralandırma formatını koru: [1], [2], vb.
- Her numaralı öğeyi ayrı çevir, birleştirme
- Boş satır veya çok kısa öğeleri de çevir, atlama"""


def _parse_retry_after_seconds(retry_after: str | None) -> float | None:
    """Parse Retry-After header value to seconds."""
    if not retry_after:
        return None

    # Case 1: seconds value
    try:
        seconds = float(retry_after)
        return max(seconds, 0.0)
    except ValueError:
        pass

    # Case 2: HTTP-date value
    try:
        retry_dt = parsedate_to_datetime(retry_after)
        if retry_dt.tzinfo is None:
            retry_dt = retry_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max((retry_dt - now).total_seconds(), 0.0)
    except (TypeError, ValueError, OverflowError):
        return None


def _retry_delay_seconds(attempt: int, retry_after: str | None = None) -> float:
    """Compute retry delay using Retry-After when available, otherwise exponential backoff."""
    header_delay = _parse_retry_after_seconds(retry_after)
    if header_delay is not None:
        return min(header_delay, MAX_RETRY_DELAY_SECONDS)

    exponential = min(BASE_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)), MAX_RETRY_DELAY_SECONDS)
    jitter = random.uniform(0.0, RETRY_JITTER_SECONDS)
    return exponential + jitter


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1.3 tokens per word for mixed EN/TR."""
    return int(len(text.split()) * 1.3)


def chunk_text_nodes(nodes: list[dict], max_tokens: int = 3000) -> list[list[dict]]:
    """Split text nodes into chunks that fit within token limits."""
    chunks = []
    current_chunk = []
    current_tokens = 0

    for node in nodes:
        node_tokens = estimate_tokens(node["text"])
        if current_chunk and current_tokens + node_tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = []
            current_tokens = 0
        current_chunk.append(node)
        current_tokens += node_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def format_chunk(nodes: list[dict]) -> str:
    """Format text nodes as numbered list for the API."""
    lines = []
    for i, node in enumerate(nodes):
        lines.append(f"[{i + 1}] {node['text']}")
    return "\n".join(lines)


def parse_response(response_text: str, count: int) -> dict[int, str]:
    """Parse numbered translations from API response. Returns {0: text, 1: text, ...}."""
    result = {}
    pattern = r'\[(\d+)\]\s*'
    parts = re.split(pattern, response_text.strip())

    i = 1
    while i < len(parts) - 1:
        num = int(parts[i]) - 1  # Convert to 0-indexed
        text = parts[i + 1].strip()
        result[num] = text
        i += 2

    return result


def translate_chunk(
    nodes: list[dict], model: str = DEFAULT_MODEL, api_key: str | None = None
) -> dict[int, str]:
    """Translate a chunk of text nodes via OpenRouter API."""
    if api_key is None:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set. Set it in .env or environment.")

    user_message = format_chunk(nodes)

    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = httpx.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "epub-translator",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.3,
                },
                timeout=120.0,
            )
        except httpx.RequestError:
            if attempt >= MAX_API_ATTEMPTS:
                raise
            time.sleep(_retry_delay_seconds(attempt))
            continue

        if response.status_code in RETRYABLE_STATUS_CODES:
            if attempt >= MAX_API_ATTEMPTS:
                response.raise_for_status()
            time.sleep(_retry_delay_seconds(attempt, response.headers.get("Retry-After")))
            continue

        response.raise_for_status()
        data = response.json()
        translated_text = data["choices"][0]["message"]["content"]
        return parse_response(translated_text, count=len(nodes))

    # Unreachable due to return/raise paths above.
    raise RuntimeError("Translation failed after retries.")


def translate_nodes(
    nodes: list[dict],
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    max_tokens: int = 3000,
    on_chunk_done: callable = None,
) -> dict[int, str]:
    """Translate all text nodes, chunking as needed. Returns {global_index: translated_text}."""
    chunks = chunk_text_nodes(nodes, max_tokens=max_tokens)
    all_translations = {}

    for chunk_idx, chunk in enumerate(chunks):
        local_translations = translate_chunk(chunk, model=model, api_key=api_key)

        for local_idx, translated in local_translations.items():
            if local_idx < len(chunk):
                global_idx = chunk[local_idx]["index"]
                all_translations[global_idx] = translated

        if on_chunk_done:
            on_chunk_done(chunk_idx + 1, len(chunks))

    return all_translations
