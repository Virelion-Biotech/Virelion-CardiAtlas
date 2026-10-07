# CardiAtlas 0.9.0 CPU audit

## Evidence

Baseline: `2b5969a38e053db5874eaffe60f8c6d647d5f09a` (0.8.1).
The original 101 tests passed with approximately 80.47% coverage. All 17 independently added regression cases failed on that revision. After corrections, **142 tests pass with 82.10% coverage** locally on Python 3.12.14, including actual HTTP sockets, SQLite persistence, CLI execution, metadata reconstruction, graph-locked release transitions and 30 generated digest-invariance examples.

The reference build now includes all 21 records, including the previously unloadable optical records. Every record passes declared runtime types and generated JSON Schema. Both selected-source replay and fresh live NCBI checks pass:

* Eight GSE153480 sample accessions match GSM4644949–GSM4644956.
* All eight are explicitly scRNA; surgery labels reconstruct MI/reference and post-surgical timepoints day1/day3. Developmental age remains separate raw metadata.
* All eight lack explicit biological subject IDs: zero reconstructed subjects, **benchmark readiness blocked**. No animal identity was invented from accessions or titles.
* All five catalog accessions resolve to exact live Series entries; titles, taxon and GEO sample inventories are recorded with provenance. GSE269054 contains both human and mouse metadata and carries a mixed-species blocker. GEO samples are not biological replicate counts.
* All six optical PMID/title/DOI/year records match PubMed, including the declared review classification. This checks bibliographic identity, not extracted claim accuracy.

[results.json](results.json) records source-fixture replay; [live-results.json](live-results.json) records fresh NCBI checks. [fixtures/provenance.json](fixtures/provenance.json) records original URLs, retrieval date, full decompressed GEO metadata SHA-256 and the selected fixture SHA-256. The selected fixture is deliberately not the full source file; the two digests have different meanings.

## Reproduce on CPU

```bash
python -m pip install -e '.[test]'
python -m pip install ruff
python scripts/generate_json_schemas.py --check
python -m ruff check cardiatlas tests scripts validation
python -m pytest -q --cov=cardiatlas --cov-fail-under=80
python validation/run_cpu_validation.py
python validation/run_cpu_validation.py --live --output validation/live-results.json
python -m cardiatlas reconstruct-geo GSE153480 --output /tmp/cardiatlas-geo
python -m build
```

The core package still uses only the Python standard library and needs no GPU. JSON Schema/Hypothesis/coverage/build are test tools. Network calls are explicit; source-fixture replay and unit tests are offline. CI exercises Linux Python 3.10–3.14, Windows Python 3.12, schema sync, reference builds, persistent CLI/HTTP/release integration, source replay, live NCBI checks, wheel/sdist builds and installed-runtime dependency auditing. Source outages or changed source contracts fail the live check rather than yielding a false pass.

An installed-wheel smoke test runs outside the checkout and verifies actual SQLite reopen, relationship-digest persistence, lifecycle transitions and CLI subprocesses. Runtime dependency auditing found no known vulnerabilities; the unpublished local project itself is not auditable against a PyPI advisory identity. This is not a code-security certification.

## Corrected failures

* Native record loading now enforces declared fields, types and enum values, rejects unknown fields and ambiguous/nonfinite JSON, and validates complete SQLite batches before persistent mutation.
* Study readiness scopes samples to the selected study, requires complete condition and recognized modality metadata, real tissue information and dataset membership. Duplicate condition entries no longer manufacture multiple groups.
* GEO RNA-Seq strategy alone no longer means bulk RNA. Explicit assay labels and raw source keys are preserved. Missing values fall through to other explicit metadata; conflicting/pool-like subject fields cannot count as resolved subjects. Surgery/timepoint aliases are recognized.
* GEO summary lookup selects the exact requested Series, not whichever search result appears first. Conflicting/missing matches fail. The parser version is `geo-soft-v2`.
* Release transitions compare both historical canonical record digest and new relationship digest, including source, confidence and evidence IDs. Old releases without a relationship digest require a new draft. Record-digest semantics remain unchanged.
* Closed evidence checks cover record source/evidence links and relationship citations. Invalid graph payloads cannot bypass persistent-store validation. Unresolved endpoints and uncited edges are reported as warnings.
* A supplied evidence index cannot turn missing references into supporting/refuting evidence. Without an index, claim polarity remains a caller declaration, not verified support.
* Repeated source records no longer inflate evidence counts/scores. Scores and `independent_sources` remain heuristic source-record inventory, not independent experimental replications or probabilities. Multiword retrieval reports individual matched terms and uses bounded evidence influence.
* PubMed bibliography is not automatically classified as primary experimental evidence: explicit reviews are reviews; other retrieved articles remain curated pending content review.
* Optical schema versions now match the actual 0.3 record schema. All eight optical records are included in reference builds; missing declared files fail rather than silently producing partial releases.
* NCBI requests use bounded 429/transient-server retry and rate limiting, including GEO downloads. Invalid limits/timeouts fail. A server-requested retry delay over 30 seconds is surfaced, not shortened into an early retry.
* CLI fatal input errors return actionable status-2 errors and do not commit partially loaded records. Deliberately reported partial relation-load status retains its existing valid-record persistence behavior.

## Limits that remain

The eleven core relationships have curated source labels but **no indexed evidence citations**; seven marker endpoints are external/unresolved in this small reference corpus. These are now visible release warnings. We did not invent citations or new biological facts to make the graph appear complete. The core examples are demonstration metadata, and the five catalog datasets retain unresolved subject/condition/modality metadata despite verified bibliographic inventory. GSE269054 must be scoped to a species before benchmark use.

GSE153480's donor/animal structure remains unresolved. Eight GEO samples do not prove eight biological replicates. Pooling, paired tissues, shared animals, single-cell versus single-nucleus differences, age, region and injury design require study-specific review. Broad normalization of sham/control/healthy to reference is not authorization to pool those controls.

No expert ontology gold standard, independently annotated claim corpus, retrieval relevance cohort, held-out donor dataset or clinical validation was established. Bibliographic agreement does not validate biological claims, marker specificity, effect sizes, therapeutic relevance or HeartTwin model predictions. Metadata eligibility does not prove statistical power or leakage-free split feasibility. The release `verified` state relies on caller-supplied CI information and does not independently certify source truth.

Historical parser-v1 outputs and legacy lifecycle snapshots should be regenerated/re-staged before downstream use. The source distribution includes reference/validation assets; the library wheel deliberately contains the library, so reference builds need `--root` pointing at repository or extracted source assets.

Implementation commit: `bc48dc3688fd305bf06b18cff1a65754183bb07c` (recorded before the documentation provenance commit).
