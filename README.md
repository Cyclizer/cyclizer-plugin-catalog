# Cyclizer Plugin Catalog

This is the operator-curated, read-only index for **discovering approved
external Cyclizer Plugins**. The Catalog is not an executable Plugin registry
or a repository of Plugin binaries. Plugin ZIPs remain with their publishers
and are identified by an exact GitHub Release asset URL and SHA-256 digest.

The public source repository is
`https://github.com/gsr-4325/cyclizer-plugin-catalog`.
The Catalog starts with **zero approved entries**. In particular, the
Development Journal package is not automatically approved for Catalog
distribution. Its local development documentation is never copied to this
repository.

## Structure

```text
catalog/v1/index.json                 Curated Catalog v1, currently empty
schemas/catalog-index-v1.schema.json  Exact copy of the Cyclizer Host schema
scripts/validate_catalog.py           Offline schema and metadata checks
tests/test_validate_catalog.py        Validation and policy regression tests
docs/REVIEW_POLICY.md                 Operator review and approval policy
.github/CODEOWNERS                     Proposed Catalog ownership
.github/PULL_REQUEST_TEMPLATE.md      Listing review checklist
.github/workflows/validate-catalog.yml  CI checks
requirements-dev.txt                  Standalone Catalog validator dependency
```

The schema is byte-identical to
`Cyclizer/components/cyclizer.feature.plugin-management/schemas/catalog-index-v1.schema.json`.
A test detects schema drift when the sibling Cyclizer source checkout exists.

## Local validation

Use an existing Python environment with `jsonschema` installed:

```powershell
cd D:\Downloads\Workspace\cyclizer-plugin-catalog
python scripts\validate_catalog.py
python -m unittest discover -s tests -v
```

The validator prints `VALID_CATALOG_NOT_PUBLISHED`, the current entry
count, and the SHA-256 digest of the actual JSON bytes. It rejects duplicate
identities, duplicate package/version pairs, invalid SHA-256 values,
non-immutable source revisions, unsafe distribution URL formats and
unsorted entries.

**Passing validation is not curator approval.** It does not contact a live
Release, verify the Release ZIP's bytes, audit Plugin code, or install/activate
anything.

## Listing a Plugin

1. A publisher prepares a public, reviewed Plugin Package v2 archive and
   makes it available as a GitHub Release asset.
2. A proposal adds complete, accurate metadata to
   `catalog/v1/index.json`: package and publisher identities, supported
   Host API/OS, requested capabilities, immutable source commit, release
   URL, exact package version and the archive's actual SHA-256.
3. The operator reviews source provenance, license, capabilities, real
   download bytes and installation behavior in an isolated Cyclizer Host.
4. CI validates the metadata. A curator explicitly approves the PR and
   updates the Catalog revision and timestamp. Configure branch protection
   to require CODEOWNERS review; a CODEOWNERS file alone is insufficient.
5. A specific immutable Git commit's JSON is fetched and checked against its
   SHA-256 before explicit operator import into Cyclizer. Merely merging
   a Catalog PR does not synchronize or activate a user's Plugins.

The complete policy is in [docs/REVIEW_POLICY.md](docs/REVIEW_POLICY.md).

## Hosting

The versioned JSON is hosted **directly from this GitHub repository**.
GitHub Pages, a separate marketplace backend, and arbitrary HTML hosting
are not required. An approved import pins the complete Catalog commit SHA:

```text
https://raw.githubusercontent.com/gsr-4325/cyclizer-plugin-catalog/<CATALOG_COMMIT_SHA>/catalog/v1/index.json
```

The angle-bracketed value is explanatory, not a valid published URI. The
exact JSON digest is supplied independently during the explicit
curator-controlled import. Avoid mutable branch references for trusted import.

## Development Journal privacy

Development Journal is a developer-local Plugin. Its purpose is to render
the host checkout's `docs/plans` directly within Cyclizer; it must **not**
publish these documents to this Catalog, another Plugin repository, GitHub
Pages, a public website, or a Release ZIP. Plugin metadata and the
actual local documents are separate concerns.

## Engineering language

Documentation, source comments, test names, and Git commit subjects/bodies
are written in English, following Cyclizer's
`docs/architecture/repository-language-versioning-and-change-policy.md`.
Product localization and user-owned content are a separate concern.
