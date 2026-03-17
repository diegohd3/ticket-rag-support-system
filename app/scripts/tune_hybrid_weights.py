from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.application.services.query_analyzer import QueryAnalyzer
from app.application.services.retrieval_metrics import hit_at_k, ndcg_at_k, reciprocal_rank
from app.application.services.ticket_search_service import TicketSearchService
from app.infrastructure.ai.openai_embedding_provider import OpenAIEmbeddingProvider
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.infrastructure.db.session import SessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tune hybrid retrieval weights over labeled dataset.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="evaluation/retrieval_eval_dataset.json",
        help="Path to labeled dataset.",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-k used for metric computation.")
    parser.add_argument("--min-text-weight", type=float, default=0.1)
    parser.add_argument("--max-text-weight", type=float, default=0.9)
    parser.add_argument("--step", type=float, default=0.1)
    parser.add_argument(
        "--json-output",
        type=str,
        default="",
        help="Optional JSON output for all explored configurations.",
    )
    return parser.parse_args()


def _evaluate_config(
    search_service: TicketSearchService,
    dataset: list[dict],
    k: int,
) -> dict:
    rows: list[dict] = []
    for case in dataset:
        query = case["query"]
        expected = case["expected_ticket_ids"]
        retrieved = [
            item.ticket.ticket_id for item in search_service.search(query_text=query, limit=k)
        ]
        rows.append(
            {
                "hit_at_k": hit_at_k(retrieved, expected, k),
                "mrr": reciprocal_rank(retrieved, expected, k),
                "ndcg_at_k": ndcg_at_k(retrieved, expected, k),
            }
        )

    size = len(rows) or 1
    return {
        "hit_at_k": round(sum(item["hit_at_k"] for item in rows) / size, 4),
        "mrr": round(sum(item["mrr"] for item in rows) / size, 4),
        "ndcg_at_k": round(sum(item["ndcg_at_k"] for item in rows) / size, 4),
    }


def tune_weights(
    dataset_path: Path,
    k: int,
    min_text_weight: float,
    max_text_weight: float,
    step: float,
) -> dict:
    settings = get_settings()
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    embedding_provider = OpenAIEmbeddingProvider(settings=settings)

    results: list[dict] = []
    with SessionLocal() as session:
        repository = SqlAlchemyTicketRepository(session)

        current = min_text_weight
        while current <= max_text_weight + 1e-9:
            text_weight = round(current, 4)
            semantic_weight = round(max(0.0, 1.0 - text_weight), 4)

            search_service = TicketSearchService(
                repository=repository,
                analyzer=QueryAnalyzer(),
                embedding_provider=embedding_provider,
                candidate_limit=settings.search_candidate_limit,
                semantic_candidate_limit=settings.semantic_candidate_limit,
                semantic_search_enabled=settings.semantic_search_enabled,
                text_weight=text_weight,
                semantic_weight=semantic_weight,
                rerank_enabled=settings.rerank_enabled,
                rerank_window=settings.rerank_window,
            )
            aggregate = _evaluate_config(search_service=search_service, dataset=dataset, k=k)
            results.append(
                {
                    "text_weight": text_weight,
                    "semantic_weight": semantic_weight,
                    **aggregate,
                }
            )
            current += step

    best = sorted(
        results,
        key=lambda item: (item["ndcg_at_k"], item["mrr"], item["hit_at_k"]),
        reverse=True,
    )[0]
    return {
        "dataset_path": str(dataset_path),
        "k": k,
        "num_cases": len(dataset),
        "explored": results,
        "best": best,
    }


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    report = tune_weights(
        dataset_path=dataset_path,
        k=args.k,
        min_text_weight=args.min_text_weight,
        max_text_weight=args.max_text_weight,
        step=args.step,
    )
    best = report["best"]
    print(
        f"Best weights -> text={best['text_weight']} semantic={best['semantic_weight']} "
        f"| hit@k={best['hit_at_k']} mrr={best['mrr']} ndcg@k={best['ndcg_at_k']}"
    )

    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Tuning report written to: {output_path}")


if __name__ == "__main__":
    main()
