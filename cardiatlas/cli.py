from __future__ import annotations

import argparse
import json
import sys

from .adapters import geo_summary_to_dataset, pubmed_summary_to_evidence
from .models import EvidenceRecord
from .ncbi import NcbiClient
from .service import AtlasService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cardiatlas", description="Query and populate the Virelion cardiac knowledge layer.")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("pubmed", help="search PubMed and emit normalized evidence records")
    search.add_argument("term")
    search.add_argument("--limit", type=int, default=20)
    geo = sub.add_parser("geo", help="search GEO through NCBI and emit normalized dataset records")
    geo.add_argument("term")
    geo.add_argument("--limit", type=int, default=20)
    explain = sub.add_parser("explain", help="show a JSON record payload")
    explain.add_argument("record_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = NcbiClient()
    service = AtlasService.empty()
    if args.command == "pubmed":
        result = client.search_pubmed(args.term, args.limit)
        records: list[EvidenceRecord] = [pubmed_summary_to_evidence(item) for uid, item in result["summaries"].items() if uid != "uids"]
        for record in records:
            service.add(record)
        print(json.dumps([record.to_dict() for record in records], indent=2, sort_keys=True))
        return 0
    if args.command == "geo":
        result = client.search_geo(args.term, args.limit)
        records = [geo_summary_to_dataset(item) for uid, item in result["summaries"].items() if uid != "uids"]
        for record in records:
            service.add(record)
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
