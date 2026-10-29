from __future__ import annotations

import argparse
import json
from pathlib import Path

from cardiatlas.loader import read_bundle
from cardiatlas.service import AtlasService


def evaluate(records_path: str, benchmark_path: str, k: int = 5) -> dict[str, object]:
    if k < 1:
        raise ValueError("k must be positive")
    service = AtlasService.empty()
    service.add_many(read_bundle([records_path]))
    cases = [json.loads(line) for line in Path(benchmark_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases:
        raise ValueError("benchmark contains no queries")
    hits_at_k = 0
    reciprocal_ranks: list[float] = []
    rows = []
    for case in cases:
        relevant = set(case["relevant_ids"])
        results = service.retrieve(case["query"], limit=k)
        ranked = [item.record.id for item in results]
        rank = next((index + 1 for index, item in enumerate(ranked) if item in relevant), None)
        hits_at_k += int(rank is not None)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)
        rows.append({"query": case["query"], "relevant_ids": sorted(relevant), "ranked_ids": ranked, "first_relevant_rank": rank})
    return {
        "query_count": len(cases), "k": k, "hit_rate_at_k": hits_at_k / len(cases),
        "recall_at_k": hits_at_k / len(cases), "mrr_at_k": sum(reciprocal_ranks) / len(cases),
        "benchmark_type": "small, versioned smoke benchmark; not an expert relevance gold standard",
        "results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CardiAtlas lexical retrieval against a versioned JSONL query set.")
    parser.add_argument("--records", default="data/reference/cardiatlas_gse132880.jsonl")
    parser.add_argument("--benchmark", default="data/benchmarks/cardiatlas_retrieval_smoke.jsonl")
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = evaluate(args.records, args.benchmark, args.k)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["hit_rate_at_k"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
