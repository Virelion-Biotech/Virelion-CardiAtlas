from __future__ import annotations

from validation.run_cpu_validation import _taxon_species_set


def test_taxon_set_normalizes_mixed_species_separator_and_order():
    assert _taxon_species_set("Homo sapiens; Mus musculus") == _taxon_species_set(
        "Mus musculus, Homo sapiens"
    )


def test_taxon_set_preserves_real_mixed_species_difference():
    assert _taxon_species_set("Homo sapiens; Mus musculus") != _taxon_species_set(
        "Homo sapiens"
    )


def test_taxon_set_normalizes_known_common_species_aliases():
    assert _taxon_species_set("human; mouse") == _taxon_species_set(
        "Mus musculus, Homo sapiens"
    )



def test_taxon_set_normalizes_and_separator():
    assert _taxon_species_set("human and mouse") == _taxon_species_set(
        "Homo sapiens; Mus musculus"
    )
