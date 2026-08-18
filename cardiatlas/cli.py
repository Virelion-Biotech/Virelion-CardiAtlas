from __future__ import annotations

import argparse
import json
import sys

from .acquisition import acquisition_plan
from .adapters import geo_summary_to_dataset, pubmed_summary_to_evidence
from .build import build_reference
from .corpus_promote import promote_harvest
from .harvest_manifest import create_harvest_manifest
from .harvest_store import write_harvest
from .harvester import harvest_plan
from .identifiers import resolve as resolve_identifier
from .models import EvidenceRecord
from .ncbi import NcbiClient
from .ontology import concepts_by_category, resolve_concept
from .release_checks import assess_release
from .service import AtlasService


def _concept_payload(concept):
    return {"id": concept.id, "label": concept.label, "category": concept.category, "synonyms": list(concept.synonyms), "parent_id": concept.parent_id}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cardiatlas", description="Query and populate the Virelion cardiac knowledge layer.")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("pubmed", help="search PubMed and emit normalized evidence records")
    search.add_argument("term")
    search.add_argument("--limit", type=int, default=20)
    geo = sub.add_parser("geo", help="search GEO through NCBI and emit normalized dataset records")
    geo.add_argument("term")
    geo.add_argument("--limit", type=int, default=20)
    harvest = sub.add_parser("harvest", help="execute the bounded public acquisition plan")
    harvest.add_argument("--domain", default=None)
    harvest.add_argument("--limit", type=int, default=20)
    harvest.add_argument("--plan-only", action="store_true")
    harvest.add_argument("--output", default=None, help="directory for deduplicated harvest items, normalized records, and manifest")
    promote = sub.add_parser("promote-harvest", help="promote a harvested artifact into an Atlas candidate corpus")
    promote.add_argument("input")
    promote.add_argument("--output", required=True)
    resolve = sub.add_parser("resolve", help="resolve a cardiac term to a canonical Atlas concept")
    resolve.add_argument("term")
    identifier = sub.add_parser("identifier", help="resolve a gene symbol, accession, or PMID")
    identifier.add_argument("value")
    identifier.add_argument("--type", dest="identifier_type", default=None)
    ontology = sub.add_parser("ontology", help="list controlled cardiac concepts")
    ontology.add_argument("--category", default=None)
    release = sub.add_parser("release-check", help="run release integrity checks on the current in-memory service")
    build = sub.add_parser("build-reference", help="build the checked-in reference Atlas and emit a manifest")
    build.add_argument("--root", default=".")
    build.add_argument("--version", default="0.4.0")
    explain = sub.add_parser("explain", help="show a JSON record payload from an in-memory service")
    explain.add_argument("record_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = AtlasService.empty()

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
        result = assess_release(service.registry.all())
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.passed else 1

    if args.command == "build-reference":
        result = build_reference(args.root, args.version)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.readiness.passed else 1

    if args.command == "promote-harvest":
        report = promote_harvest(args.input, args.output)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["rejected_record_count"] == 0 else 1

    if args.command == "harvest":
        targets = acquisition_plan(args.domain)
        if args.plan_only:
            print(json.dumps([target.to_dict() for target in targets], indent=2, sort_keys=True))
            return 0
        client = NcbiClient()
        batches = harvest_plan(client, targets, limit=args.limit)
        items = [item for batch in batches for item in batch.items]
        records = [record for batch in batches for record in batch.records]
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

    if args.command == "explain":
        try:
            print(json.dumps(service.explain(args.record_id), indent=2, sort_keys=True))
        except KeyError:
            print(f"record not loaded: {args.record_id}", file=sys.stderr)
            return 1
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
