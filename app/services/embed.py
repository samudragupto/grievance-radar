# Embedding generation using sentence-transformers.

import hashlib
import logging
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_INSTANCE = None
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_embedding_model(model_name: Optional[str] = None):
    """Retrieve or initialize the SentenceTransformer model singleton.

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        SentenceTransformer model instance or mock fallback if dependency unavailable.
    """
    global _MODEL_INSTANCE, _MODEL_NAME
    target_name = model_name or _MODEL_NAME

    if _MODEL_INSTANCE is None:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading sentence-transformers model: %s", target_name)
            _MODEL_INSTANCE = SentenceTransformer(target_name)
        except Exception as e:
            logger.error(
                "Could not load SentenceTransformer ('%s'): %s. Using deterministic fallback.",
                target_name,
                e,
            )
            _MODEL_INSTANCE = None

    return _MODEL_INSTANCE


def generate_embeddings(
    texts: List[str],
    model_name: Optional[str] = None,
    batch_size: int = 32,
) -> np.ndarray:
    """Generate normalized 384-dimensional dense vectors for text complaints.

    Args:
        texts: List of complaint text strings.
        model_name: Optional custom embedding model identifier.
        batch_size: Processing batch size.

    Returns:
        numpy.ndarray of shape (len(texts), 384) with float32 embeddings.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_embedding_model(model_name)

    if model is not None:
        try:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return np.asarray(embeddings, dtype=np.float32)
        except Exception as err:
            logger.error("Error during embedding generation: %s. Falling back.", err)

    # Fallback deterministic bag-of-words / hash based 384-dim normalized vector
    # Ensures tests and environments without PyTorch/HuggingFace still execute gracefully
    logger.warning("Generating deterministic fallback embeddings for %d texts", len(texts))
    vectors = []
    for text in texts:
        vec = np.zeros(384, dtype=np.float32)
        words = text.lower().split()
        for w in words:
            # blake2b (not the builtin hash()) so the fallback is stable across
            # processes: Python string hashing is salted per-process unless
            # PYTHONHASHSEED is pinned, which made test runs non-reproducible.
            digest = hashlib.blake2b(w.encode("utf-8"), digest_size=4).digest()
            idx = int.from_bytes(digest, "big") % 384
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        vectors.append(vec)

    return np.asarray(vectors, dtype=np.float32)
