"""Offline Catalog contract tests; never contact GitHub or a Product Host."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_catalog import (
    DEFAULT_INDEX,
    DEFAULT_SCHEMA,
    CatalogValidationError,
    load_json,
    main,
    validate_catalog,
)

ROOT = Path(__file__).resolve().parents[1]
FAKE_SHA = "0123456789abcdef0123456789abcdef01234567"
FAKE_DIGEST = "a" * 64


def fake_entry(name: str = "example.demo") -> dict:
    # Synthetic, NONEXISTENT addresses: tests do not imply publication or approval.
    return {
        "id": name,
        "package_id": name,
        "title": "Synthetic Plugin",
        "summary": "Offline validator fixture, not an approved listing.",
        "publisher": {"id": "example.publisher", "name": "Example"},
        "host": {"api": "^1.0", "os": ["windows"]},
        "requested_capabilities": [],
        "scm": {
            "kind": "git",
            "hosting": "github",
            "repository_uri": "https://github.com/example/synthetic",
            "revision": FAKE_SHA,
        },
        "distribution": {
            "kind": "github-release",
            "uri": "https://github.com/example/synthetic/releases/download/v1.0.0/synthetic.cyclizer.plugin.zip",
            "version": "1.0.0",
            "sha256": FAKE_DIGEST,
        },
    }


class CatalogValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original, self.original_bytes = load_json(DEFAULT_INDEX)

    def check_payload(self, payload: dict) -> tuple[dict, str]:
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "index.json"
            index.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return validate_catalog(index)

    def test_empty_bootstrap_is_exactly_not_an_approval(self) -> None:
        value, digest = validate_catalog()
        self.assertEqual(value["schema_version"], 1)
        self.assertEqual(value["catalog_id"], "cyclizer.official")
        self.assertEqual(value["entries"], [])
        self.assertIn("unpublished", value["revision"])
        self.assertEqual(digest, hashlib.sha256(self.original_bytes).hexdigest())
        self.assertEqual(main([]), 0)

    def test_structurally_valid_synthetic_listing_passes_metadata_checks(self) -> None:
        candidate = copy.deepcopy(self.original)
        candidate["entries"] = [fake_entry()]
        parsed, _ = self.check_payload(candidate)
        self.assertEqual(len(parsed["entries"]), 1)

    def test_rejects_wrong_schema_or_extra_fields(self) -> None:
        for edit in (
            {"schema_version": 2},
            {"unexpected": True},
            {"entries": [{"id": "incomplete"}]},
            {"catalog_id": "BAD ID"},
            {"generated_at": "not-a-date"},
        ):
            with self.subTest(edit=edit):
                candidate = copy.deepcopy(self.original)
                candidate.update(edit)
                with self.assertRaises(CatalogValidationError):
                    self.check_payload(candidate)

    def test_rejects_duplicate_ids_and_duplicate_package_version(self) -> None:
        candidate = copy.deepcopy(self.original)
        candidate["entries"] = [fake_entry(), fake_entry()]
        with self.assertRaisesRegex(CatalogValidationError, "Duplicate Catalog entry"):
            self.check_payload(candidate)
        candidate["entries"][1]["id"] = "example.second"
        with self.assertRaisesRegex(CatalogValidationError, "Duplicate package/version"):
            self.check_payload(candidate)

    def test_rejects_unpinned_git_and_unsafe_release_urls(self) -> None:
        bad_urls = (
            "http://github.com/example/synthetic/releases/download/v1.0.0/x.cyclizer.plugin.zip",
            "https://evil.example/release/download/x.zip",
            "https://github.com/example/synthetic/releases/download/v1.0.0/x.cyclizer.plugin.zip?token=secret",
            "https://github.com/example/synthetic/releases/download/v1.0.0/x.zip",
            "https://user:secret@github.com/example/synthetic/releases/download/v1.0.0/x.cyclizer.plugin.zip",
            "https://github.com/example/synthetic/releases/download/v1.0.0/../x.cyclizer.plugin.zip",
        )
        for url in bad_urls:
            with self.subTest(url=url):
                candidate = copy.deepcopy(self.original)
                candidate["entries"] = [fake_entry()]
                candidate["entries"][0]["distribution"]["uri"] = url
                with self.assertRaises(CatalogValidationError):
                    self.check_payload(candidate)

        candidate = copy.deepcopy(self.original)
        candidate["entries"] = [fake_entry()]
        candidate["entries"][0]["scm"]["revision"] = "main"
        with self.assertRaisesRegex(CatalogValidationError, "commit SHA"):
            self.check_payload(candidate)

    def test_rejects_missing_digest_and_unsorted_entries(self) -> None:
        candidate = copy.deepcopy(self.original)
        candidate["entries"] = [fake_entry("example.z"), fake_entry("example.a")]
        with self.assertRaisesRegex(CatalogValidationError, "sorted"):
            self.check_payload(candidate)
        candidate["entries"] = [fake_entry()]
        candidate["entries"][0]["distribution"]["sha256"] = "abc"
        with self.assertRaises(CatalogValidationError):
            self.check_payload(candidate)

    def test_rejects_ambiguous_json_and_oversized_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.json"
            bad.write_text('{"revision": "one", "revision": "two"}', encoding="utf-8")
            with self.assertRaisesRegex(CatalogValidationError, "Duplicate JSON key"):
                load_json(bad)
            bad.write_bytes(b"x" * (4 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(CatalogValidationError, "exceeds"):
                load_json(bad)

    def test_standalone_schema_is_canonical_copy_when_sibling_cyclizer_exists(self) -> None:
        upstream = (
            ROOT.parent
            / "Cyclizer"
            / "components"
            / "cyclizer.feature.plugin-management"
            / "schemas"
            / "catalog-index-v1.schema.json"
        )
        if not upstream.is_file():
            self.skipTest("Cyclizer sibling checkout unavailable on CI")
        self.assertEqual(
            DEFAULT_SCHEMA.read_bytes(),
            upstream.read_bytes(),
            "Catalog Schema drifted from the Cyclizer Host contract",
        )

    def test_sibling_cyclizer_production_host_accepts_empty_catalog(self) -> None:
        cyclizer = ROOT.parent / "Cyclizer"
        executable = cyclizer / ".venv" / "Scripts" / "python.exe"
        if not executable.is_file():
            executable = cyclizer / ".venv" / "bin" / "python"
        if not executable.is_file() or not (cyclizer / "src").is_dir():
            self.skipTest("No sibling Cyclizer Python Host environment on CI")
        script = (
            "import hashlib,sys;from pathlib import Path;"
            "sys.path.insert(0,sys.argv[1]);"
            "from cyclizer_next.host.plugin_package_management import PluginPackageService;"
            "from cyclizer_next.kernel.component_manifest import load_component_manifest;"
            "root=Path(sys.argv[2]);index=Path(sys.argv[3]).read_bytes();"
            "service=PluginPackageService(root,host_api_version='1.0.0',"
            "component_manifest_validator=load_component_manifest);"
            "snapshot=service.refresh_catalog(index,"
            "source_uri='https://raw.githubusercontent.com/gsr-4325/cyclizer-plugin-catalog/"
            + FAKE_SHA
            + "/catalog/v1/index.json',source_revision='"
            + FAKE_SHA
            + "',expected_sha256=hashlib.sha256(index).hexdigest());"
            "assert snapshot.catalog_id=='cyclizer.official';"
            "assert len(snapshot.entries)==0"
        )
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    str(executable),
                    "-c",
                    script,
                    str(cyclizer / "src"),
                    directory,
                    str(DEFAULT_INDEX),
                ],
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
