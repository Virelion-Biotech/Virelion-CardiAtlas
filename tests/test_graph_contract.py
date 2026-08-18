import pytest

from cardiatlas.graph import AtlasGraph, Relation


def test_controlled_predicate_and_deduplicated_edges():
    graph = AtlasGraph()
    graph.add(Relation("marker:tnnt2", "marks", "cell:cardiomyocyte", ("e1",), 0.9))
    graph.add(Relation("marker:tnnt2", "marks", "cell:cardiomyocyte", ("e2",), 0.95))
    relation = graph.relations("marks")[0]
    assert relation.evidence_ids == ("e1", "e2")
    assert relation.confidence == 0.95
    assert graph.neighbors("marker:tnnt2") == ["cell:cardiomyocyte"]


def test_unknown_predicate_rejected():
    with pytest.raises(ValueError, match="unsupported relationship predicate"):
        AtlasGraph().add(Relation("a", "invented", "b"))


def test_subgraph_does_not_duplicate_edges():
    graph = AtlasGraph([
        Relation("a", "associated_with", "b"),
        Relation("b", "associated_with", "c"),
    ])
    assert len(graph.subgraph("a", hops=2)) == 2
