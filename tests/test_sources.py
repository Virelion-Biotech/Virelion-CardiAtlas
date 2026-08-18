from dataclasses import dataclass

from cardiatlas.models import MarkerRecord
from cardiatlas.sources import SourceResult, ingest_source


@dataclass
class FakeSource:
    name: str = "fake"

    def search(self, query: str, limit: int = 20) -> SourceResult:
        return SourceResult(
            source_name=self.name,
            query=query,
            records=(MarkerRecord(id="marker:tnnt2", name="TNNT2", entity_id="TNNT2"),),
            retrieved_at="2026-01-01T00:00:00Z",
        )


def test_source_adapter_contract():
    result = ingest_source(FakeSource(), "TNNT2", 1)
    assert result.source_name == "fake"
    assert result.records[0].id == "marker:tnnt2"
