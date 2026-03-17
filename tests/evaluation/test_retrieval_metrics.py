from app.application.services.retrieval_metrics import hit_at_k, ndcg_at_k, reciprocal_rank


def test_hit_at_k_returns_one_when_expected_in_top_k() -> None:
    retrieved = ["A", "B", "C"]
    expected = ["X", "B"]
    assert hit_at_k(retrieved, expected, k=2) == 1.0


def test_hit_at_k_returns_zero_when_expected_not_in_top_k() -> None:
    retrieved = ["A", "B", "C"]
    expected = ["X", "Y"]
    assert hit_at_k(retrieved, expected, k=3) == 0.0


def test_reciprocal_rank() -> None:
    retrieved = ["A", "B", "C"]
    expected = ["C"]
    assert reciprocal_rank(retrieved, expected, k=3) == 1 / 3


def test_ndcg_at_k_perfect_ranking() -> None:
    retrieved = ["T1", "T2", "T3"]
    expected = ["T1", "T2"]
    assert ndcg_at_k(retrieved, expected, k=2) == 1.0


def test_ndcg_at_k_zero_when_no_relevant_items() -> None:
    retrieved = ["A", "B", "C"]
    expected = ["X"]
    assert ndcg_at_k(retrieved, expected, k=3) == 0.0
