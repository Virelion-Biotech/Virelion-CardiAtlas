# CardiAtlas architecture

## Layers

### Domain layer
`models.py` defines the stable record contract. Records are intentionally small and serializable. Rich relationships belong in the graph rather than being embedded recursively inside records.

### Semantics layer
`ontology.py` resolves common cardiac terms to canonical IDs. `normalize.py` handles conservative text and identifier normalization. Unknown terms remain unresolved.

### Evidence layer
`evidence.py` scores evidence transparently. `claims.py` represents assertions and conflicting evidence. A claim is not treated as settled solely because one source exists.

### Graph layer
`graph.py` stores typed relationships with optional provenance and confidence. This makes multi-hop biological context queryable without hard-coding every relationship into downstream models.

### Retrieval layer
`search.py` provides deterministic lexical search. `query.py` adds structured filters and scoring. This layer is intentionally dependency-free so it can be replaced by a database index or vector/graph service later.

### Persistence layer
`sqlite.py` provides a local backend for reproducible workflows. It persists records, edges and release manifests while keeping the application-facing contracts independent of SQLite.

### Integration layer
`integrations.py` converts dataset records into a portable CardiBench candidate. `contracts.py` defines a versioned `AtlasContext` payload for inter-repository exchange.

### Release layer
`release.py` canonicalizes records and computes deterministic SHA-256 digests. A release therefore identifies both a logical Atlas version and the exact record content represented by it.

## Recommended data flow

```text
source
  |
  v
adapter
  |
  v
normalize -> validate -> provenance
  |             |
  |             +--> reject / quarantine
  v
Atlas record
  |
  +--> graph relationship(s)
  |
  +--> evidence / claim linkage
  |
  v
quality gate
  |
  +--> accepted Atlas state
  |
  +--> CardiBench candidate export
  |
  v
release snapshot
```

## Design rule

Do not make downstream consumers depend on the current SQLite schema, NCBI implementation, or Python dataclass internals. The public boundary is the record contract, relation contract, release manifest, and `AtlasContext` contract.
