from cardiatlas.models import DatasetRecord
from cardiatlas.schema import RELATION_TYPES
from cardiatlas.service import AtlasService


def test_reconstruct_study_records_study_has_dataset_not_dataset_has_study():
    """Regression test: AtlasService.reconstruct_study used to record the
    dataset<->study edge backwards, as dataset --has_study--> study, using a
    predicate that isn't even in RELATION_TYPES. docs/data-model.md defines
    the controlled direction as study --has_dataset--> dataset.
    """
    service = AtlasService.empty()
    dataset = DatasetRecord(
        id="dataset:GSE100",
        name="Example GEO",
        accession="GSE100",
        repository="GEO",
        study_title="Example cardiac study",
        organism="Sus scrofa",
        tissue="heart",
    )
    service.add(dataset)
    rows = [{"accession": "GSM1", "group": "MI", "subject_id": "1", "timepoint": "day 3", "modality": "snRNA-seq"}]

    study, samples, report = service.reconstruct_study(dataset.id, rows)

    # Every relation this call records must use a controlled predicate.
    all_relations = service.graph.subgraph(study.id, hops=1)
    assert all_relations
    for relation in all_relations:
        assert relation.predicate in RELATION_TYPES

    has_dataset = [r for r in all_relations if r.predicate == "has_dataset"]
    assert len(has_dataset) == 1
    assert has_dataset[0].subject == study.id
    assert has_dataset[0].object == dataset.id

    assert "has_study" not in {r.predicate for r in all_relations}

    has_sample_from_study = [r for r in service.graph.subgraph(study.id, hops=1) if r.predicate == "has_sample" and r.subject == study.id]
    assert {r.object for r in has_sample_from_study} == {sample.id for sample in samples}

    has_sample_from_dataset = [r for r in service.graph.subgraph(dataset.id, hops=1) if r.predicate == "has_sample" and r.subject == dataset.id]
    assert {r.object for r in has_sample_from_dataset} == {sample.id for sample in samples}
