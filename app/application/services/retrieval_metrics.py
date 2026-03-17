from __future__ import annotations

from math import log2


def hit_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    expected_set = set(expected)
    return 1.0 if any(ticket_id in expected_set for ticket_id in top_k) else 0.0


def reciprocal_rank(retrieved: list[str], expected: list[str], k: int) -> float:
    if k <= 0:
        return 0.0
    expected_set = set(expected)
    for idx, ticket_id in enumerate(retrieved[:k], start=1):
        if ticket_id in expected_set:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    if k <= 0:
        return 0.0
    expected_set = set(expected)
    dcg = 0.0
    for idx, ticket_id in enumerate(retrieved[:k], start=1):
        rel = 1.0 if ticket_id in expected_set else 0.0
        if rel > 0:
            dcg += rel / log2(idx + 1)

    ideal_rels = [1.0] * min(len(expected_set), k)
    idcg = 0.0
    for idx, rel in enumerate(ideal_rels, start=1):
        idcg += rel / log2(idx + 1)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg
