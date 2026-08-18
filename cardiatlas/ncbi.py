from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(slots=True)
class NcbiClient:
    """Small NCBI E-utilities client using only the Python standard library."""

    tool: str = "virelion-cardi-atlas"
    email: str | None = None
    api_key: str | None = None
    timeout: float = 30.0
    min_interval: float = 0.34
    _last_request: float = 0.0

    def _request(self, endpoint: str, params: dict[str, str]) -> bytes:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        query = {"tool": self.tool, **params}
        if self.email:
            query["email"] = self.email
        if self.api_key:
            query["api_key"] = self.api_key
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" + endpoint + "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(url, headers={"User-Agent": self.tool})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = response.read()
        self._last_request = time.monotonic()
        return payload

    def esearch(self, db: str, term: str, retmax: int = 20) -> list[str]:
        payload = self._request("esearch.fcgi", {"db": db, "term": term, "retmode": "json", "retmax": str(retmax)})
        document = json.loads(payload.decode("utf-8"))
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
