"""
In-memory semantic search over project examples seeded from GitHub.

Examples are stored as JSON files in backend/data/project_examples/.
Each file contains pre-computed embeddings (1536-dim) so search is fast
(numpy cosine similarity, no DB call, ~1-5ms for 40 files).

To rebuild the library:
    python -m scripts.seed_from_github
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np

from rag.corpus import embed

log = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data" / "project_examples"

# Lazy-loaded cache: list of dicts with keys title, content, embedding, metadata
_cache: Optional[List[Dict]] = None


def _load() -> List[Dict]:
    global _cache
    if _cache is not None:
        return _cache
    examples = []
    for f in sorted(_DATA_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text())
            if "embedding" in d and "content" in d:
                examples.append(d)
        except Exception as exc:
            log.warning("Could not load project example %s: %s", f.name, exc)
    _cache = examples
    log.info("Loaded %d project examples from disk", len(examples))
    return _cache


def invalidate_cache() -> None:
    """Force reload on next search (call after seed_from_github completes)."""
    global _cache
    _cache = None


async def search(query: str, top_k: int = 2) -> List[Dict]:
    """
    Return the top_k most similar project examples to the query.

    Returns an empty list (and logs a warning) if no examples are loaded,
    so callers continue gracefully without crashing the pipeline.
    """
    examples = _load()
    if not examples:
        log.warning("No project examples found in %s — skipping few-shot context", _DATA_DIR)
        return []

    query_vec = np.array(await embed(query), dtype=np.float32)
    matrix = np.array([ex["embedding"] for ex in examples], dtype=np.float32)

    # Batch cosine similarity
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vec) + 1e-9
    similarities = matrix @ query_vec / norms

    top_indices = np.argsort(similarities)[::-1][:top_k]
    return [
        {
            "title": examples[i]["title"],
            "content": examples[i]["content"],
            "similarity": float(similarities[i]),
        }
        for i in top_indices
    ]
