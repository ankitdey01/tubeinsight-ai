"""
backend/utils/preprocessing.py
────────────────────────────────
Comment cleaning and preprocessing utilities.
Removes spam, URLs, and prepares text for embedding + analysis.
"""
print(f"[LOADING] {__file__}")

import re
import html
from loguru import logger


# ─── Filters ──────────────────────────────────────────────────────────────────

MIN_COMMENT_LENGTH = 4     # Skip very short comments like "nice", "👍"
MAX_COMMENT_LENGTH = 1000      # Truncate very long comments
SPAM_PATTERNS = [
    r"check out my channel",
    r"subscribe to me",
    r"follow me",
    r"first!+$",
    r"^\d+$",                  # Pure numbers
]


def clean_text(text: str) -> str:
    """Clean a single comment text."""
    # Decode HTML entities
    text = html.unescape(text)

    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip and truncate
    text = text.strip()[:MAX_COMMENT_LENGTH]

    return text


def is_valid_comment(text: str) -> bool:
    """Return True if comment is worth keeping."""
    if len(text) < MIN_COMMENT_LENGTH:
        return False

    # Check spam patterns
    lower = text.lower()
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, lower):
            return False

    # Skip pure emoji comments
    no_emoji = re.sub(r"[^\w\s]", "", text)
    if len(no_emoji.strip()) < 5:
        return False

    return True


def preprocess_comments(comments: list[dict]) -> list[dict]:
    """
    Clean and filter a list of raw comment objects.
    Returns filtered list ready for embedding.
    """
    cleaned = []
    skipped = 0

    for comment in comments:
        raw_text = comment.get("text", "")
        clean = clean_text(raw_text)

        if not is_valid_comment(clean):
            skipped += 1
            continue

        cleaned.append({**comment, "text": clean})

    logger.info(
        f"Preprocessing: {len(comments)} raw → {len(cleaned)} clean "
        f"({skipped} filtered)"
    )
    return cleaned


def chunk_comments_for_llm(
    comments: list[dict],
    max_chars: int = 8000,
    max_per_chunk: int = 50,
) -> list[str]:
    """
    Batch comments into chunks that fit in an LLM context window.
    Returns list of formatted text blocks.
    """
    chunks = []
    current_chunk = []
    current_len = 0

    for i, comment in enumerate(comments):
        text = comment.get("text", "")
        formatted = f"[Comment {i+1}] {text}"
        text_len = len(formatted)

        if (current_len + text_len > max_chars or len(current_chunk) >= max_per_chunk) and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_len = 0

        current_chunk.append(formatted)
        current_len += text_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks
