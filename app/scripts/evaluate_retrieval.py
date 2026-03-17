from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import httpx

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
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality on a labeled dataset.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="evaluation/retrieval_eval_dataset.json",
        help="Path to JSON dataset with query/expected_ticket_ids.",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-K window used for metrics.")
    parser.add_argument(
        "--mode",
        choices=["api", "db"],
        default="api",
        help="Use API endpoint mode or direct DB mode.",
    )
    parser.add_argument(
        "--api-base-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL for API mode.",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        default="",
        help="Optional output path to store aggregate JSON results.",
    )
    return parser.parse_args()


def evaluate_cases(
    dataset: list[dict],
    k: int,
    retrieve_fn: Callable[[str, int], list[str]],
) -> dict:
    case_results: list[dict] = []
    for case in dataset:
        query = case["query"]
        expected = case["expected_ticket_ids"]
        retrieved = retrieve_fn(query, k)

        case_results.append(
            {
                "query": query,
                "expected_ticket_ids": expected,
                "retrieved_ticket_ids": retrieved,
                "hit_at_k": round(hit_at_k(retrieved, expected, k), 4),
                "mrr": round(reciprocal_rank(retrieved, expected, k), 4),
                "ndcg_at_k": round(ndcg_at_k(retrieved, expected, k), 4),
            }
        )

    count = len(case_results) or 1
    return {
        "k": k,
        "num_cases": len(case_results),
        "hit_at_k": round(sum(item["hit_at_k"] for item in case_results) / count, 4),
        "mrr": round(sum(item["mrr"] for item in case_results) / count, 4),
        "ndcg_at_k": round(sum(item["ndcg_at_k"] for item in case_results) / count, 4),
        "cases": case_results,
    }


def run_evaluation_api(dataset: list[dict], k: int, api_base_url: str) -> dict:
    def retrieve(query_text: str, top_k: int) -> list[str]:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{api_base_url}/api/v1/tickets/search",
                params={"query": query_text, "limit": top_k},
            )
            response.raise_for_status()
            payload = response.json()
            return [item["ticket_id"] for item in payload["results"]]

    return evaluate_cases(dataset=dataset, k=k, retrieve_fn=retrieve)


def run_evaluation_db(dataset: list[dict], k: int) -> dict:
    settings = get_settings()

    with SessionLocal() as session:
        repository = SqlAlchemyTicketRepository(
            session,
            vector_probes=settings.vector_search_probes,
        )
        search_service = TicketSearchService(
            repository=repository,
            analyzer=QueryAnalyzer(),
            embedding_provider=OpenAIEmbeddingProvider(settings),
            candidate_limit=settings.search_candidate_limit,
            semantic_candidate_limit=settings.semantic_candidate_limit,
            semantic_search_enabled=settings.semantic_search_enabled,
            text_weight=settings.hybrid_text_weight,
            semantic_weight=settings.hybrid_semantic_weight,
        )

        def retrieve(query_text: str, top_k: int) -> list[str]:
            ranked = search_service.search(query_text=query_text, limit=top_k)
            return [entry.ticket.ticket_id for entry in ranked]

        return evaluate_cases(dataset=dataset, k=k, retrieve_fn=retrieve)


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if args.mode == "api":
        aggregate = run_evaluation_api(dataset=dataset, k=args.k, api_base_url=args.api_base_url)
    else:
        aggregate = run_evaluation_db(dataset=dataset, k=args.k)

    aggregate["mode"] = args.mode
    aggregate["dataset_path"] = str(dataset_path)

    print(
        f"Retrieval evaluation mode={args.mode} @k={aggregate['k']} "
        f"over {aggregate['num_cases']} cases | "
        f"hit@k={aggregate['hit_at_k']} mrr={aggregate['mrr']} ndcg@k={aggregate['ndcg_at_k']}"
    )

    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
        print(f"Detailed JSON report written to: {output_path}")


if __name__ == "__main__":
    main()
