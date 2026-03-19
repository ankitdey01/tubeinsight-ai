"""
backend/core/embeddings.py
───────────────────────────
Embedding pipeline using local sentence-transformers.
No API calls required - runs completely offline.
"""
print(f"[LOADING] {__file__}")

import numpy as np
from loguru import logger

# Lazy loading of the model - only loaded when first used
_model = None

def _get_model():
    """Lazy load the sentence-transformer model."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model (first time)...")
        try:
            from sentence_transformers import SentenceTransformer
            # Use a lightweight but effective model
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.success("Sentence-transformer model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
    return _model


class EmbeddingClient:
    def __init__(self):
        self.batch_size = 128  # Larger batch size for local processing
        self._model = None

    def _get_model(self):
        """Get or load the embedding model."""
        if self._model is None:
            self._model = _get_model()
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts using local sentence-transformers.
        Returns list of embedding vectors in same order.
        """
        if not texts:
            return []

        model = self._get_model()
        
        logger.info(f"Embedding {len(texts)} texts locally")
        
        # Process in batches to avoid memory issues
        all_embeddings = []
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

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string for RAG retrieval."""
        model = self._get_model()
        embedding = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        return embedding[0].tolist()
