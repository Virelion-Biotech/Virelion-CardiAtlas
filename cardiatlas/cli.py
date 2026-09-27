from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .acquisition import acquisition_plan
from .adapters import geo_summary_to_dataset, pubmed_summary_to_evidence
from .build import build_reference
from .corpus import corpus_report
from .corpus_promote import promote_harvest
from .export import write_cardiBench_candidates, write_records, write_release
from .geo_harvest import reconstruct_geo_accession, write_geo_bundle
from .graph import Relation
from .harvest_manifest import create_harvest_manifest
from .harvest_store import write_harvest
from .harvester import harvest_plan
from .identifiers import resolve as resolve_identifier
from .loader import read_bundle, record_from_dict
from .models import DatasetRecord, EvidenceRecord
from .ncbi import NcbiClient
from .ontology import concepts_by_category, resolve_concept
from .release_checks import assess_release
from .release_lifecycle import create_draft, deprecate, promote_to_candidate, verify
from .schema import RELATION_TYPES
from .service import AtlasService
from .sqlite import SQLiteAtlasStore

# Commands that accept a persistent SQLite store, either as a required
# positional "db" (load/search/context/export -- these are meaningless
# without one) or an optional "--db" flag (everything else -- kept
# ephemeral/in-memory by default so existing zero-argument behavior is
# unchanged). "release" manages its own store lifecycle separately below
# and is deliberately not in this set.
_DB_BACKED_COMMANDS = {
    "corpus", "explain", "release-check",
    "pubmed", "geo", "harvest", "promote-harvest",
    "reconstruct-study", "reconstruct-geo",
    "load", "search", "context", "export",
}


def _concept_payload(concept):
    return {"id": concept.id, "label": concept.label, "category": concept.category, "synonyms": list(concept.synonyms), "parent_id": concept.parent_id}


def _read_metadata(path: str) -> list[dict[str, object]]:
    source = Path(path)
    if source.suffix.lower() == ".jsonl":
        rows: list[dict[str, object]] = []
        with source.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"JSONL row {line_number} is not an object")
                rows.append(payload)
        return rows
    if source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise ValueError("JSON metadata must contain an array of objects")
        return payload
    if source.suffix.lower() == ".csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise ValueError("metadata input must be .json, .jsonl, or .csv")


def _read_relations_jsonl(path: str) -> list[Relation]:
    relations: list[Relation] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            payload = json.loads(line)
            try:
                relations.append(Relation(
                    subject=payload["subject"],
                    predicate=payload["predicate"],
                    object=payload["object"],
                    evidence_ids=tuple(payload.get("evidence_ids", ())),
                    confidence=payload.get("confidence"),
                    source=payload.get("source"),
                ))
            except KeyError as exc:
                raise ValueError(f"relation on line {line_number} is missing required field: {exc}") from exc
    return relations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cardiatlas", description="Query and populate the Virelion cardiac knowledge layer.")
    sub = parser.add_subparsers(dest="command", required=True)

    pubmed_cmd = sub.add_parser("pubmed", help="search PubMed and emit normalized evidence records")
    pubmed_cmd.add_argument("term")
    pubmed_cmd.add_argument("--limit", type=int, default=20)
    pubmed_cmd.add_argument("--db", default=None, help="persist results into this CardiAtlas SQLite store")

    geo_cmd = sub.add_parser("geo", help="search GEO through NCBI and emit normalized dataset records")
    geo_cmd.add_argument("term")
    geo_cmd.add_argument("--limit", type=int, default=20)
    geo_cmd.add_argument("--db", default=None, help="persist results into this CardiAtlas SQLite store")

    harvest_cmd = sub.add_parser("harvest", help="execute the bounded public acquisition plan")
    harvest_cmd.add_argument("--domain", default=None)
    harvest_cmd.add_argument("--limit", type=int, default=20)
    harvest_cmd.add_argument("--plan-only", action="store_true")
    harvest_cmd.add_argument("--output", default=None, help="directory for deduplicated harvest items, normalized records, and manifest")
    harvest_cmd.add_argument("--db", default=None, help="also persist harvested records into this CardiAtlas SQLite store")

    promote_cmd = sub.add_parser("promote-harvest", help="promote a harvested artifact into an Atlas candidate corpus")
    promote_cmd.add_argument("input")
    promote_cmd.add_argument("--output", required=True)
    promote_cmd.add_argument("--db", default=None, help="also persist promoted records into this CardiAtlas SQLite store")

    reconstruct_cmd = sub.add_parser("reconstruct-study", help="reconstruct a GEO study and samples from tabular metadata")
    reconstruct_cmd.add_argument("dataset", help="JSON file containing one DatasetRecord")
    reconstruct_cmd.add_argument("metadata", help="sample metadata as CSV, JSON, or JSONL")
    reconstruct_cmd.add_argument("--output", required=True, help="output directory for study, samples, and reconstruction report")
    reconstruct_cmd.add_argument("--db", default=None, help="also persist the dataset/study/samples into this CardiAtlas SQLite store")

    live_cmd = sub.add_parser("reconstruct-geo", help="fetch GEO family SOFT metadata and reconstruct a live GSE accession")
    live_cmd.add_argument("accession")
    live_cmd.add_argument("--output", required=True, help="output directory for dataset, study, samples, and report")
    live_cmd.add_argument("--db", default=None, help="also persist the dataset/study/samples into this CardiAtlas SQLite store")

    corpus_cmd = sub.add_parser("corpus", help="report on the current corpus (in-memory, or a persistent store with --db)")
    corpus_cmd.add_argument("--db", default=None)

    resolve_cmd = sub.add_parser("resolve", help="resolve a cardiac term to a canonical Atlas concept")
    resolve_cmd.add_argument("term")

    identifier_cmd = sub.add_parser("identifier", help="resolve a gene symbol, accession, or PMID")
    identifier_cmd.add_argument("value")
    identifier_cmd.add_argument("--type", dest="identifier_type", default=None)

    ontology_cmd = sub.add_parser("ontology", help="list controlled cardiac concepts")
    ontology_cmd.add_argument("--category", default=None)

    release_check_cmd = sub.add_parser("release-check", help="run release integrity checks (in-memory, or a persistent store with --db)")
    release_check_cmd.add_argument("--db", default=None)

    lifecycle = sub.add_parser("release", help="manage the draft/candidate/verified/deprecated release lifecycle against a persistent store")
    lifecycle_sub = lifecycle.add_subparsers(dest="release_command", required=True)
    stage = lifecycle_sub.add_parser("stage", help="stage a new draft release from everything currently in the store")
    stage.add_argument("db", help="path to a CardiAtlas SQLite store")
    stage.add_argument("--version", required=True)
    stage.add_argument("--schema-version", default=None)
    lifecycle_promote = lifecycle_sub.add_parser("promote", help="draft -> candidate: structural checks must pass")
    lifecycle_promote.add_argument("db")
    lifecycle_promote.add_argument("version")
    verify_cmd = lifecycle_sub.add_parser("verify", help="candidate -> verified: requires a passing CI run on an exact commit")
    verify_cmd.add_argument("db")
    verify_cmd.add_argument("version")
    verify_cmd.add_argument("--commit", required=True, dest="commit_sha", help="the exact commit the release was built from")
    verify_cmd.add_argument("--ci-passed", action="store_true", help="confirm CI passed on that commit (required to verify)")
    verify_cmd.add_argument("--require-benchmark-ready", action="store_true", help="also require every study in the release to pass its benchmark-readiness gate")
    deprecate_cmd = lifecycle_sub.add_parser("deprecate", help="mark a release deprecated, retained for reproducibility")
    deprecate_cmd.add_argument("db")
    deprecate_cmd.add_argument("version")
    deprecate_cmd.add_argument("--superseded-by", required=True)
    deprecate_cmd.add_argument("--note", default="")
    show = lifecycle_sub.add_parser("show", help="show a stored release's current lifecycle state")
    show.add_argument("db")
    show.add_argument("version")
    list_cmd = lifecycle_sub.add_parser("list", help="list stored releases, optionally filtered by state")
    list_cmd.add_argument("db")
    list_cmd.add_argument("--state", default=None, choices=["draft", "candidate", "verified", "deprecated"])

    build_cmd = sub.add_parser("build-reference", help="build the checked-in reference Atlas and emit a manifest")
    build_cmd.add_argument("--root", default=".")
    build_cmd.add_argument("--version", default="0.4.0")

    explain_cmd = sub.add_parser("explain", help="show a JSON record payload, its evidence, and its graph neighborhood")
    explain_cmd.add_argument("record_id")
    explain_cmd.add_argument("--db", default=None)

    load_cmd = sub.add_parser("load", help="ingest one or more JSONL record bundles (and optionally relations) into a persistent store")
    load_cmd.add_argument("db")
    load_cmd.add_argument("paths", nargs="+", help="one or more JSONL files of Atlas records")
    load_cmd.add_argument("--relations", default=None, help="a JSONL file of relations: {subject, predicate, object, evidence_ids?, confidence?, source?}")

    search_cmd = sub.add_parser("search", help="lexical, evidence-aware search over a persistent store")
    search_cmd.add_argument("db")
    search_cmd.add_argument("query")
    search_cmd.add_argument("--type", dest="record_type", default=None, help="restrict to one record_type")
    search_cmd.add_argument("--limit", type=int, default=20)
    search_cmd.add_argument("--context", action="store_true", help="also include each hit's graph neighborhood")
    search_cmd.add_argument("--hops", type=int, default=1, help="neighborhood hops when --context is set")

    context_cmd = sub.add_parser("context", help="show a record's graph neighborhood in a persistent store")
    context_cmd.add_argument("db")
    context_cmd.add_argument("record_id")
    context_cmd.add_argument("--hops", type=int, default=2)

    export_cmd = sub.add_parser("export", help="export everything in a persistent store to a file")
    export_cmd.add_argument("db")
    export_cmd.add_argument("output")
    export_cmd.add_argument("--type", dest="record_type", default=None, help="restrict to one record_type")
    export_cmd.add_argument("--release-version", default=None, help="write a release bundle (manifest + records) at this version instead of a bare JSONL")
    export_cmd.add_argument("--benchmark-candidates", action="store_true", help="export DatasetRecords as CardiBench candidates instead")

    return parser


def _dispatch(args: argparse.Namespace, service: AtlasService) -> int:
    if args.command == "corpus":
        print(json.dumps(corpus_report(service.registry.all()).to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "resolve":
        concept = resolve_concept(args.term)
        if concept is None:
            print(json.dumps({"resolved": False, "input": args.term}, indent=2))
            return 1
        print(json.dumps({"resolved": True, "concept": _concept_payload(concept)}, indent=2, sort_keys=True))
        return 0

    if args.command == "identifier":
        resolution = resolve_identifier(args.value, args.identifier_type)
        print(json.dumps({"query": resolution.query, "canonical_id": resolution.canonical_id, "identifier_type": resolution.identifier_type, "confidence": resolution.confidence, "matched_alias": resolution.matched_alias, "source": resolution.source}, indent=2, sort_keys=True))
        return 0 if resolution.canonical_id else 1

    if args.command == "ontology":
        concepts = concepts_by_category(args.category) if args.category else concepts_by_category("cell_type") + concepts_by_category("cell_state") + concepts_by_category("phenotype") + concepts_by_category("process")
        print(json.dumps([_concept_payload(item) for item in concepts], indent=2, sort_keys=True))
        return 0

    if args.command == "release-check":
        result = assess_release(service.registry.all(), service.graph.relations())
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.passed else 1

    if args.command == "build-reference":
        result = build_reference(args.root, args.version)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.readiness.passed else 1

    if args.command == "promote-harvest":
        report = promote_harvest(args.input, args.output)
        promoted_path = Path(args.output) / "records.jsonl"
        if promoted_path.exists():
            service.add_many(read_bundle([promoted_path]))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["rejected_record_count"] == 0 else 1

    if args.command == "reconstruct-study":
        payload = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
        dataset = record_from_dict(payload)
        if not isinstance(dataset, DatasetRecord):
            raise ValueError("dataset input must describe a DatasetRecord")
        service.add(dataset)
        rows = _read_metadata(args.metadata)
        study, samples, report = service.reconstruct_study(dataset.id, rows)
        target = Path(args.output)
        target.mkdir(parents=True, exist_ok=True)
        (target / "study.json").write_text(json.dumps(study.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with (target / "samples.jsonl").open("w", encoding="utf-8") as handle:
            for sample in samples:
                handle.write(json.dumps(sample.to_dict(), sort_keys=True) + "\n")
        (target / "report.json").write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "reconstruct-geo":
        client = NcbiClient()
        bundle = reconstruct_geo_accession(client, args.accession)
        write_geo_bundle(bundle, args.output)
        # Mirror AtlasService.reconstruct_study's has_dataset/has_sample
        # relations so a live GEO reconstruction is just as queryable
        # in-process (or via --db) as a reconstruct-study call, not only
        # available as files on disk.
        service.add(bundle.dataset)
        service.add(bundle.study)
        service.add_many(list(bundle.samples))
        service.relate(bundle.study.id, "has_dataset", bundle.dataset.id, confidence=1.0, source="cardiatlas:geo-reconstruction")
        for sample in bundle.samples:
            service.relate(bundle.study.id, "has_sample", sample.id, confidence=1.0, source="cardiatlas:geo-reconstruction")
            service.relate(bundle.dataset.id, "has_sample", sample.id, confidence=1.0, source="cardiatlas:geo-reconstruction")
        print(json.dumps(bundle.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "harvest":
        targets = acquisition_plan(args.domain)
        if args.plan_only:
            print(json.dumps([target.to_dict() for target in targets], indent=2, sort_keys=True))
            return 0
        client = NcbiClient()
        batches = harvest_plan(client, targets, limit=args.limit)
        items = [item for batch in batches for item in batch.items]
        records = [record for batch in batches for record in batch.records]
        service.add_many(records)
        manifest = create_harvest_manifest(items, version="1.0")
        if args.output:
            manifest = write_harvest(items, args.output, version="1.0", created_at=manifest.created_at, records=records)
        payload = {
            "target_count": len(batches),
            "record_count": len(records),
            "item_count": len(items),
            "manifest": manifest.to_dict(),
            "output": args.output,
            "batches": [batch.to_dict() for batch in batches],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if manifest.qc.passed else 1

    if args.command == "explain":
        try:
            print(json.dumps(service.explain(args.record_id), indent=2, sort_keys=True))
        except KeyError:
            print(f"record not loaded: {args.record_id}", file=sys.stderr)
            return 1
        return 0

    if args.command == "load":
        records = read_bundle(args.paths)
        service.add_many(records)
        relation_count = 0
        rejected: list[str] = []
        if args.relations:
            for relation in _read_relations_jsonl(args.relations):
                if relation.predicate not in RELATION_TYPES:
                    rejected.append(f"{relation.subject} --{relation.predicate}--> {relation.object}")
                    continue
                service.relate(relation.subject, relation.predicate, relation.object, relation.evidence_ids, relation.confidence, relation.source)
                relation_count += 1
        print(json.dumps({
            "db": args.db,
            "records_loaded": len(records),
            "relations_loaded": relation_count,
            "relations_rejected": rejected,
        }, indent=2, sort_keys=True))
        return 0 if not rejected else 1

    if args.command == "search":
        if args.context:
            results = service.retrieve_with_context(args.query, hops=args.hops, limit=args.limit)
            if args.record_type:
                results = [r for r in results if r["result"]["record"]["record_type"] == args.record_type]
            print(json.dumps(results, indent=2, sort_keys=True))
        else:
            results = service.retrieve(args.query, record_type=args.record_type, limit=args.limit)
            print(json.dumps([r.to_dict() for r in results], indent=2, sort_keys=True))
        return 0

    if args.command == "context":
        print(json.dumps(service.context(args.record_id, hops=args.hops), indent=2, sort_keys=True))
        return 0

    if args.command == "export":
        if args.benchmark_candidates:
            datasets = [r for r in service.registry.all("dataset") if isinstance(r, DatasetRecord)]
            count = write_cardiBench_candidates(datasets, args.output)
            print(json.dumps({"output": args.output, "candidate_count": count}, indent=2, sort_keys=True))
            return 0
        records = service.registry.all(args.record_type)
        if args.release_version:
            manifest = write_release(records, args.output, args.release_version)
            print(json.dumps({"output": args.output, "manifest": manifest}, indent=2, sort_keys=True))
        else:
            count = write_records(records, args.output)
            print(json.dumps({"output": args.output, "record_count": count}, indent=2, sort_keys=True))
        return 0

    client = NcbiClient()
    if args.command == "pubmed":
        result = client.search_pubmed(args.term, args.limit)
        records: list[EvidenceRecord] = [pubmed_summary_to_evidence(item) for uid, item in result["summaries"].items() if uid != "uids"]
        service.add_many(records)
        print(json.dumps([record.to_dict() for record in records], indent=2, sort_keys=True))
        return 0

    if args.command == "geo":
        result = client.search_geo(args.term, args.limit)
        records = [geo_summary_to_dataset(item) for uid, item in result["summaries"].items() if uid != "uids"]
        service.add_many(records)
        print(json.dumps([record.to_dict() for record in records], indent=2, sort_keys=True))
        return 0

    return 2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "release":
        with SQLiteAtlasStore(args.db) as store:
            if args.release_command == "stage":
                records = store.all_records()
                relations = store.graph().relations()
                kwargs = {"schema_version": args.schema_version} if args.schema_version else {}
                release = create_draft(records, args.version, relations, **kwargs)
                store.save_release_record(release)
                print(json.dumps(release.to_dict(), indent=2, sort_keys=True))
                return 0 if release.readiness.passed else 1

            if args.release_command == "list":
                print(json.dumps(store.list_release_records(args.state), indent=2, sort_keys=True))
                return 0

            existing = store.get_release_record(args.version)
            if existing is None:
                print(f"no release staged for version {args.version!r} in {args.db}", file=sys.stderr)
                return 1

            if args.release_command == "promote":
                records = store.all_records()
                relations = store.graph().relations()
                try:
                    release = promote_to_candidate(existing, records, relations)
                except ValueError as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
                store.save_release_record(release)
                print(json.dumps(release.to_dict(), indent=2, sort_keys=True))
                return 0

            if args.release_command == "verify":
                records = store.all_records()
                relations = store.graph().relations()
                try:
                    release = verify(
                        existing, records, relations,
                        commit_sha=args.commit_sha, ci_passed=args.ci_passed,
                        require_benchmark_ready=args.require_benchmark_ready,
                    )
                except ValueError as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
                store.save_release_record(release)
                print(json.dumps(release.to_dict(), indent=2, sort_keys=True))
                return 0

            if args.release_command == "deprecate":
                try:
                    release = deprecate(existing, superseded_by=args.superseded_by, note=args.note)
                except ValueError as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
                store.save_release_record(release)
                print(json.dumps(release.to_dict(), indent=2, sort_keys=True))
                return 0

            if args.release_command == "show":
                print(json.dumps(existing.to_dict(), indent=2, sort_keys=True))
                return 0
        return 2

    db_path = getattr(args, "db", None) if args.command in _DB_BACKED_COMMANDS else None
    store: SQLiteAtlasStore | None = None
    if db_path:
        store = SQLiteAtlasStore(db_path)
        service = store.load_service()
    else:
        service = AtlasService.empty()
    try:
        return _dispatch(args, service)
    finally:
        if store is not None:
            store.save_service(service)
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
