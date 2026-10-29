from scripts.evaluate_retrieval import evaluate


def test_retrieval_evaluator_reports_full_hit_rate_for_curated_smoke_set():
    result = evaluate("data/reference/cardiatlas_gse132880.jsonl", "data/benchmarks/cardiatlas_retrieval_smoke.jsonl", k=5)
    assert result["query_count"] == 3
    assert result["hit_rate_at_k"] == 1.0
    assert 0 < result["mrr_at_k"] <= 1
