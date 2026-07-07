"""Data-source clients (direct public REST).

Each client returns domain objects that already carry `Evidence` (source + record
id + url), so provenance is attached at the point of retrieval. Runtime uses direct
REST for reproducibility; Claude Science is used at build time for curation.
"""
