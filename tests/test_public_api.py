import cardiatlas


def test_all_exports_resolve_and_are_unique():
    """Regression test: __init__.py's __all__ must list only names that are
    actually importable from the top-level package, with no duplicates and
    no stale entries. (release_lifecycle's public API and search.search/
    search_records were previously missing from __all__ entirely, despite
    every other module's API being re-exported at the top level.)
    """
    assert len(cardiatlas.__all__) == len(set(cardiatlas.__all__)), "duplicate name in __all__"
    missing = [name for name in cardiatlas.__all__ if not hasattr(cardiatlas, name)]
    assert not missing, f"__all__ lists names that don't resolve: {missing}"


def test_release_lifecycle_is_part_of_the_public_api():
    assert cardiatlas.RELEASE_STATES == ("draft", "candidate", "verified", "deprecated")
    assert cardiatlas.create_draft is not None
    assert cardiatlas.promote_to_candidate is not None
    assert cardiatlas.verify_release is not None
    assert cardiatlas.deprecate is not None


def test_atlas_service_quickstart_example_works():
    """Regression test for the README quickstart, which called the bare,
    argument-less AtlasService() -- but AtlasService is a plain dataclass
    with required fields, so that always raised TypeError. AtlasService.empty()
    is the correct zero-argument constructor.
    """
    service = cardiatlas.AtlasService.empty()
    assert service.resolve("MI") == "phenotype:myocardial_infarction"
