# Unit tests for clustering services.

from app.services.cluster import cluster_complaints
from app.services.embed import generate_embeddings


def test_clustering_returns_valid_labels(sample_complaints):
    """Verify all complaints receive valid non-empty cluster label assignments."""
    texts = [c["text"] for c in sample_complaints]
    embeddings = generate_embeddings(texts)
    results = cluster_complaints(embeddings, texts, algo="kmeans")

    assert "labels" in results
    assert len(results["labels"]) == len(texts)
    assert len(results["clusters"]) > 0


def test_kmeans_fallback_works_when_bertopic_fails(sample_complaints):
    """Verify fallback executes smoothly when BERTopic raises or is specified."""
    texts = [c["text"] for c in sample_complaints[:30]]
    embeddings = generate_embeddings(texts)
    results = cluster_complaints(embeddings, texts, algo="non_existent_or_fail")

    assert "labels" in results
    assert len(results["labels"]) == 30
    assert "clusters" in results


def test_cluster_count_is_reasonable(sample_complaints):
    """Verify number of discovered clusters remains within acceptable municipal bounds."""
    texts = [c["text"] for c in sample_complaints]
    embeddings = generate_embeddings(texts)
    results = cluster_complaints(embeddings, texts, algo="kmeans")

    cluster_count = len(results["clusters"])
    assert 2 <= cluster_count <= 25


def test_auto_labels_are_non_empty_strings(sample_complaints):
    """Verify generated TF-IDF cluster labels are descriptive strings."""
    texts = [c["text"] for c in sample_complaints]
    embeddings = generate_embeddings(texts)
    results = cluster_complaints(embeddings, texts, algo="kmeans")

    for c in results["clusters"]:
        assert isinstance(c["label"], str)
        assert len(c["label"].strip()) > 0
