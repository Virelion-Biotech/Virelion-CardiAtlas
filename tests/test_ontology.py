from cardiatlas.ontology import canonical_concept_id, concepts_by_category, resolve_concept


def test_synonym_resolution():
    assert canonical_concept_id("MI") == "phenotype:myocardial_infarction"
    assert canonical_concept_id("cardiac myocyte") == "cell:cardiomyocyte"


def test_unknown_concept_returns_none():
    assert resolve_concept("totally unknown cardiac thing") is None


def test_categories_are_nonempty():
    assert concepts_by_category("cell_type")
    assert concepts_by_category("phenotype")
