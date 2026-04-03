"""
backend/core/embeddings.py
───────────────────────────
Embedding pipeline using local sentence-transformers.
No API calls required - runs completely offline.
"""
print(f"[LOADING] {__file__}")

from typing import List, Optional, Any
from loguru import logger
from config.settings import get_settings

def _get_model() -> Any:
    """Lazy load the sentence-transformer model, using model name from settings."""
    if not hasattr(_get_model, "_model"):
        logger.info("Loading sentence-transformer model (first time)...")
        try:
            from sentence_transformers import SentenceTransformer
            settings = get_settings()
            model_name = getattr(settings, "sentence_transformer_model", "all-MiniLM-L6-v2")
            logger.info(f"Using sentence-transformer model: {model_name}")
            _get_model._model = SentenceTransformer(model_name)
            logger.success("Sentence-transformer model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
    return _get_model._model


class EmbeddingClient:
    """
    Local embedding client using sentence-transformers.

    Uses the all-MiniLM-L6-v2 model which provides a good balance of
    speed and quality. Embeddings are 384-dimensional vectors.

    Features:
    - Lazy model loading (only loads on first use)
    - Batch processing to handle large volumes efficiently
    - No API calls or external dependencies at runtime
    """

    def __init__(self) -> None:
        self.batch_size: int = 128  # Larger batch size for local processing
        self._model: Optional[Any] = None

    def _get_model(self) -> Any:
        """Get or load the embedding model."""
        if self._model is None:
            self._model = _get_model()
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts using local sentence-transformers.

        Args:
            texts: List of strings to embed

        Returns:
            List of embedding vectors (384-dim) in same order as input
        """
        if not texts:
            return []

        model = self._get_model()

        logger.info(f"Embedding {len(texts)} texts locally")

        # Process in batches to avoid memory issues
        all_embeddings: List[List[float]] = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1

            # Encode batch
            embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
            all_embeddings.extend(embeddings.tolist())

            logger.debug(f"Batch {batch_num}/{total_batches} done")

        logger.success(f"Embedded {len(all_embeddings)} texts locally")
        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query string for RAG retrieval.

        Args:
            query: The search query to embed

        Returns:
            384-dimensional embedding vector
        """
        model = self._get_model()
        embedding = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        return embedding[0].tolist()
