# Unit tests for embedding generation.

import importlib.util

import numpy as np
import pytest

from app.services.embed import generate_embeddings

# Semantic-quality assertions only hold for the real transformer model; the
# offline fallback is a bag-of-words hash and carries no semantic signal.
REAL_MODEL_AVAILABLE = importlib.util.find_spec("sentence_transformers") is not None
requires_real_model = pytest.mark.skipif(
    not REAL_MODEL_AVAILABLE,
    reason="sentence-transformers is not installed; the fallback encoder is not semantic",
)


def test_generate_embeddings_shape():
    """Verify embeddings produce expected (n, 384) dimensional matrix."""
    texts = [
        "Water supply shortage in Ward 4.",
        "Streetlights are completely off in the school lane.",
        "Garbage pile is overflowing and creating foul smell.",
    ]
    embeddings = generate_embeddings(texts)
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 384)


def test_embeddings_are_normalized():
    """Verify generated vector embeddings have approximately unit Euclidean norm."""
    texts = ["Broken water pipe in junction."]
    embeddings = generate_embeddings(texts)
    norm = np.linalg.norm(embeddings[0])
    assert pytest.approx(norm, 0.05) == 1.0


def test_identical_texts_produce_identical_embeddings():
    """Verify deterministic embedding results for exact same strings."""
    t1 = "Overflowing drain near market area in Ward 2."
    t2 = "Overflowing drain near market area in Ward 2."
    emb = generate_embeddings([t1, t2])
    np.testing.assert_allclose(emb[0], emb[1], rtol=1e-5, atol=1e-5)


@requires_real_model
def test_similar_texts_have_higher_cosine_similarity():
    """Verify semantically similar sentences have higher cosine similarity than unrelated ones."""
    t_base = "Water supply is not reaching our houses since 3 days."
    t_sim = "No drinking water available from pipeline for three days."
    t_diff = "Potholes on the road damaged car suspension."

    emb = generate_embeddings([t_base, t_sim, t_diff])
    sim_related = np.dot(emb[0], emb[1]) / (np.linalg.norm(emb[0]) * np.linalg.norm(emb[1]))
    sim_unrelated = np.dot(emb[0], emb[2]) / (np.linalg.norm(emb[0]) * np.linalg.norm(emb[2]))

    assert sim_related > sim_unrelated
