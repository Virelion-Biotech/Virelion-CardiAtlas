from __future__ import annotations

import gzip
import json
import re
import time
import math
import urllib.error
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(slots=True)
class NcbiClient:
    """Small NCBI E-utilities/GEO metadata client using only the Python standard library."""

    tool: str = "virelion-cardi-atlas"
    email: str | None = None
    api_key: str | None = None
    timeout: float = 30.0
    min_interval: float = 0.34
    _last_request: float = 0.0
    max_retries: int = 2

    def _request(self, endpoint: str, params: dict[str, str]) -> bytes:
        query = {"tool": self.tool, **params}
        if self.email:
            query["email"] = self.email
        if self.api_key:
            query["api_key"] = self.api_key
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" + endpoint + "?" + urllib.parse.urlencode(query)
        return self._url_payload(url)

    def __post_init__(self):
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        if not math.isfinite(self.min_interval) or self.min_interval < 0:
            raise ValueError("min_interval must be finite and nonnegative")
        if type(self.max_retries) is not int or not 0 <= self.max_retries <= 5:
            raise ValueError("max_retries must be an integer between 0 and 5")

    def _url_payload(self, url: str) -> bytes:
        for attempt in range(self.max_retries + 1):
            elapsed = time.monotonic() - self._last_request
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            request = urllib.request.Request(url, headers={"User-Agent": self.tool})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return response.read()
            except urllib.error.HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt == self.max_retries:
                    raise
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                try:
                    delay = float(retry_after)
                except ValueError:
                    try:
                        date = parsedate_to_datetime(retry_after)
                        delay = (date - datetime.now(timezone.utc)).total_seconds()
                    except (ValueError, TypeError, OverflowError):
                        delay = float(2 ** attempt)
                if not math.isfinite(delay):
                    delay = float(2 ** attempt)
                # Refuse a long server-requested delay rather than retry too early.
                if delay > 30:
                    raise
                exc.close()
                time.sleep(max(0.0, delay))
            finally:
                self._last_request = time.monotonic()
        raise RuntimeError("unreachable retry state")

    @staticmethod
    def geo_family_soft_url(accession: str) -> str:
        """Return the canonical NCBI FTP URL for a GEO Series family SOFT file."""
        accession = accession.strip().upper()
        if not re.fullmatch(r"GSE\d+", accession):
            raise ValueError(f"invalid GEO Series accession: {accession}")
        parent = accession[:-3] + "nnn" if len(accession) > 6 else "GSEnnn"
        return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{parent}/{accession}/soft/{accession}_family.soft.gz"

    def _geo_request(self, accession: str) -> bytes:
        url = self.geo_family_soft_url(accession)
        payload = self._url_payload(url)
        return gzip.decompress(payload)

    def fetch_geo_family_soft(self, accession: str) -> bytes:
        """Fetch only GEO family SOFT metadata for a Series accession."""
        return self._geo_request(accession)

    def esearch(self, db: str, term: str, retmax: int = 20) -> list[str]:
        if type(retmax) is not int or retmax < 0:
            raise ValueError("retmax must be a nonnegative integer")
        if retmax == 0:
            return []
        payload = self._request("esearch.fcgi", {"db": db, "term": term, "retmode": "json", "retmax": str(retmax)})
        document = json.loads(payload.decode("utf-8"))
        if "error" in document or document.get("esearchresult", {}).get("ERROR"):
            raise ValueError("NCBI esearch returned an error")
        return list(document["esearchresult"]["idlist"])

    def esummary(self, db: str, ids: list[str]) -> dict:
        if not ids:
            return {}
        payload = self._request("esummary.fcgi", {"db": db, "id": ",".join(ids), "retmode": "json"})
        return json.loads(payload.decode("utf-8"))["result"]

    def efetch_pubmed_xml(self, ids: list[str]) -> list[ET.Element]:
        if not ids:
            return []
        payload = self._request("efetch.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
        root = ET.fromstring(payload)
        return list(root.findall("PubmedArticle"))

    def search_pubmed(self, term: str, retmax: int = 20) -> dict:
        ids = self.esearch("pubmed", term, retmax)
        return {"ids": ids, "summaries": self.esummary("pubmed", ids)}

    def search_geo(self, term: str, retmax: int = 20) -> dict:
        """Search GEO datasets through NCBI's GDS database."""
        ids = self.esearch("gds", term, retmax)
        return {"ids": ids, "summaries": self.esummary("gds", ids)}
