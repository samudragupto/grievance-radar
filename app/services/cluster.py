# Complaint clustering using BERTopic with K-Means and TF-IDF fallback.

import logging
from typing import Any, Dict, List

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def _extract_tfidf_labels(texts: List[str], labels: np.ndarray, n_terms: int = 4) -> Dict[int, str]:
    """Derive representative topic labels using TF-IDF for cluster groups.

    Args:
        texts: Raw or preprocessed complaint texts.
        labels: Cluster assignment array corresponding to texts.
        n_terms: Number of top descriptive terms to include in the label.

    Returns:
        Dictionary mapping cluster ID integer to string label.
    """
    topic_labels: Dict[int, str] = {}
    unique_labels = sorted(list(set(labels)))

    for cluster_id in unique_labels:
        cluster_texts = [texts[i] for i in range(len(texts)) if labels[i] == cluster_id]
        if not cluster_texts:
            topic_labels[cluster_id] = f"Cluster {cluster_id}"
            continue

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=100,
                ngram_range=(1, 2),
            )
            tfidf_matrix = vectorizer.fit_transform(cluster_texts)
            feature_names = np.array(vectorizer.get_feature_names_out())
            scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
            top_indices = scores.argsort()[::-1][:n_terms]
            terms = [feature_names[idx].title() for idx in top_indices if scores[idx] > 0]
            if terms:
                topic_labels[cluster_id] = " | ".join(terms)
            else:
                topic_labels[cluster_id] = f"Grievance Group {cluster_id}"
        except Exception:
            topic_labels[cluster_id] = f"Issue Cluster {cluster_id}"

    return topic_labels


def _kmeans_clustering(
    embeddings: np.ndarray,
    texts: List[str],
    min_k: int = 5,
    max_k: int = 15,
) -> Dict[str, Any]:
    """Execute K-Means clustering with dynamic k selection.

    Args:
        embeddings: Dense vector representations of shape (N, D).
        texts: Corresponding complaint texts.
        min_k: Minimum clusters to evaluate.
        max_k: Maximum clusters to evaluate.

    Returns:
        Dictionary containing labels list and cluster metadata.
    """
    n_samples = len(embeddings)
    k = min(max(min_k, n_samples // 30), max_k)
    k = max(2, min(k, n_samples - 1)) if n_samples > 2 else 1

    logger.info("Executing K-Means with k=%d for %d samples", k, n_samples)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    topic_labels = _extract_tfidf_labels(texts, labels)

    cluster_meta = []
    for c_id, label in topic_labels.items():
        count = int(np.sum(labels == c_id))
        cluster_meta.append(
            {
                "id": int(c_id),
                "label": label,
                "count": count,
            }
        )

    return {
        "labels": labels.tolist(),
        "topic_labels": {int(k): v for k, v in topic_labels.items()},
        "clusters": cluster_meta,
    }


def cluster_complaints(
    embeddings: np.ndarray,
    texts: List[str],
    algo: str = "bertopic",
) -> Dict[str, Any]:
    """Cluster complaints using BERTopic with automatic fallback to K-Means.

    Args:
        embeddings: Dense vector representations of shape (N, 384).
        texts: Complaint texts.
        algo: Preferred algorithm ('bertopic' or 'kmeans').

    Returns:
        Dictionary with 'labels' array, 'topic_labels' mapping, and 'clusters' summary list.
    """
    if len(texts) == 0:
        return {"labels": [], "topic_labels": {}, "clusters": []}

    if algo.lower() == "bertopic":
        try:
            from bertopic import BERTopic

            logger.info("Attempting BERTopic clustering on %d complaints", len(texts))
            topic_model = BERTopic(
                nr_topics="auto",
                min_topic_size=max(5, len(texts) // 40),
                verbose=False,
            )
            topics, _ = topic_model.fit_transform(texts, embeddings)
            labels = np.array(topics)

            # Map negative outlier labels (-1) to positive cluster
            if -1 in labels:
                max_topic = max([t for t in labels if t != -1], default=0)
                labels = np.where(labels == -1, max_topic + 1, labels)

            topic_info = topic_model.get_topic_info()
            topic_labels: Dict[int, str] = {}
            for _, row in topic_info.iterrows():
                tid = int(row["Topic"])
                if tid == -1:
                    continue
                name = str(row.get("Name", f"Topic {tid}"))
                cleaned_name = name.split("_", 1)[-1].replace("_", " | ").title()
                topic_labels[tid] = cleaned_name or f"Topic {tid}"

            # Fill missing topic labels with TF-IDF fallback
            for tid in set(labels):
                if tid not in topic_labels:
                    topic_labels[tid] = f"Cluster {tid}"

            cluster_meta = []
            for c_id, label in topic_labels.items():
                count = int(np.sum(labels == c_id))
                if count > 0:
                    cluster_meta.append({"id": int(c_id), "label": label, "count": count})

            return {
                "labels": labels.tolist(),
                "topic_labels": topic_labels,
                "clusters": cluster_meta,
            }
        except Exception as e:
            logger.warning(
                "BERTopic unavailable or encountered error: %s. Falling back to K-Means.", e
            )

    return _kmeans_clustering(embeddings, texts)
