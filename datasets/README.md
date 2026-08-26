# Dataset Releases

The existing directories registered in `datasets/manifest.json` are read-only
historical evidence. Repository reorganization added metadata and checksum
inventories without modifying their payload or export bytes.

New runner output must be written to `artifacts/` first. Promotion into
`datasets/` requires:

1. a new versioned release ID;
2. a recorded configuration fingerprint and tool versions;
3. license review;
4. a deterministic SHA-256 inventory; and
5. explicit release approval.

The registered legacy releases remain `internal_only` and
`review_required`. Their configuration fingerprints are marked
`legacy_unavailable` rather than reconstructed after the fact.
