# SPDX-License-Identifier: Apache-2.0
import random
import numpy as np

from src.agents.guards.embedding_orthogonaliser import EmbeddingOrthogonaliser


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def test_random_projection_cosine_small() -> None:
    rng = np.random.default_rng(42)
    vec = rng.normal(size=32).astype("float32")
    ortho = EmbeddingOrthogonaliser(dim=32, steps=5000, rng=random.Random(42))
    proj = ortho.project(vec)
    assert cosine(vec, proj) < 0.1
