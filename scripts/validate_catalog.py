"""Offline Catalog v1 validation: exact Cyclizer JSON Schema plus curator policy.

This script checks metadata only. It does NOT approve any listing, access GitHub,
fetch a Release asset, install a Plugin, or modify Cyclizer Product UserDataRoot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "catalog" / "v1" / "index.json"
DEFAULT_SCHEMA = ROOT / "schemas" / "catalog-index-v1.schema.json"
MAX_INDEX_BYTES = 4 * 1024 * 1024
GIT_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


class CatalogValidationError(ValueError):
    """Malformed or unsafe Catalog metadata."""


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise CatalogValidationError(f"Duplicate JSON key: {name}")
        result[name] = value
    return result


def load_json(path: Path, *, size_limit: int = MAX_INDEX_BYTES) -> tuple[dict, bytes]:
    if path.is_symlink() or not path.is_file():
        raise CatalogValidationError(f"Missing or symlinked JSON file: {path}")
    if path.stat().st_size > size_limit:
        raise CatalogValidationError(f"JSON file exceeds {size_limit} bytes: {path}")
    data = path.read_bytes()
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CatalogValidationError(f"Invalid UTF-8 JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise CatalogValidationError(f"Top-level JSON must be an object: {path}")
    return value, data


def require_https_url(value: str, *, github_release: bool) -> None:
    try:
        parts = urlsplit(value)
        hostname = parts.hostname
        port = parts.port
    except ValueError as error:
        raise CatalogValidationError(f"Malformed URL: {value}") from error
    if (
        parts.scheme != "https"
        or not hostname
        or parts.username is not None
        or parts.password is not None
        or port not in (None, 443)
        or parts.query
        or parts.fragment
        or any(ord(char) < 33 or ord(char) == 127 or char == "\\" for char in value)
    ):
        raise CatalogValidationError(f"Expected a credential-free canonical HTTPS URL: {value}")
    if github_release:
        path = parts.path.split("/")
        if (
            hostname != "github.com"
            or len(path) != 7
            or path[0] != ""
            or path[3:5] != ["releases", "download"]
            or any(not segment or segment in {".", ".."} for segment in path[1:])
            or not path[6].endswith(".cyclizer.plugin.zip")
        ):
            raise CatalogValidationError(f"Expected a GitHub Release package ZIP URL: {value}")
    elif hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise CatalogValidationError(f"Repository must be publicly addressable: {value}")


def validate_catalog(
    index_path: Path = DEFAULT_INDEX,
    schema_path: Path = DEFAULT_SCHEMA,
) -> tuple[dict, str]:
    index, index_bytes = load_json(index_path)
    schema, _ = load_json(schema_path, size_limit=512 * 1024)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        raise CatalogValidationError(f"Invalid JSON Schema: {error}") from error
    errors = sorted(
        Draft202012Validator(schema).iter_errors(index),
        key=lambda error: (tuple(str(x) for x in error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path) or "(root)"
        raise CatalogValidationError(f"Catalog JSON Schema: {location}: {error.message}")

    if index["catalog_id"] != "cyclizer.official":
        raise CatalogValidationError("Catalog ID must remain cyclizer.official")
    try:
        timestamp = datetime.fromisoformat(index["generated_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise CatalogValidationError("generated_at must be an ISO-8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise CatalogValidationError("generated_at must include an explicit timezone")

    seen_ids: set[str] = set()
    seen_versions: set[tuple[str, str]] = set()
    for entry in index["entries"]:
        entry_id = entry["id"]
        if entry_id in seen_ids:
            raise CatalogValidationError(f"Duplicate Catalog entry ID: {entry_id}")
        seen_ids.add(entry_id)
        pair = (entry["package_id"], entry["distribution"]["version"])
        if pair in seen_versions:
            raise CatalogValidationError(
                f"Duplicate package/version: {pair[0]} {pair[1]}"
            )
        seen_versions.add(pair)
        scm = entry["scm"]
        require_https_url(scm["repository_uri"], github_release=False)
        if scm["kind"] == "git" and not GIT_SHA.fullmatch(scm["revision"]):
            raise CatalogValidationError(
                f"{entry_id}: Git source revision must be an immutable full commit SHA"
            )
        if not isinstance(scm["revision"], str) or scm["revision"].strip() != scm["revision"]:
            raise CatalogValidationError(f"{entry_id}: invalid source revision")
        require_https_url(entry["distribution"]["uri"], github_release=True)
    ids_in_file = [entry["id"] for entry in index["entries"]]
    if ids_in_file != sorted(ids_in_file):
        raise CatalogValidationError("Catalog entries must be sorted by entry ID")
    digest = hashlib.sha256(index_bytes).hexdigest()
    return index, digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        index, sha256 = validate_catalog(args.index, args.schema)
    except (CatalogValidationError, OSError) as error:
        print(f"CATALOG_REJECTED: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": "VALID_CATALOG_NOT_PUBLISHED",
                "catalog_id": index["catalog_id"],
                "revision": index["revision"],
                "entries": len(index["entries"]),
                "sha256": sha256,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
