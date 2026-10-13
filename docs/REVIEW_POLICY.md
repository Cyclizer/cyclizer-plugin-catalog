# Curated Plugin Catalog review policy

## Authority

The Catalog is an operator-maintained list of discoverable packages. A GitHub
Pull Request from a publisher is a proposal, **not** approval. The curator
must review code, provenance, licensing, capabilities and the concrete Release
archive before approving the PR. A green GitHub Actions check is only
syntactic/offline evidence. Configure a GitHub branch protection rule or
ruleset requiring the Catalog owner to review changes to `main`; a CODEOWNERS
file alone does not enforce approval.

Catalog listing is not an OS sandbox, a safety guarantee, permission to run
arbitrary code, or a grant to modify Cyclizer. Cyclizer's installer independently
checks the package and obtains user consent; the Host remains the activation
authority.

## Listing criteria

1. Publisher identity, package ID, semver and source repository must match the
   reviewed Plugin Package Manifest v2. `scm.revision` pins an actual immutable
   source commit, not `main` or a movable tag.
2. `distribution.uri` must point to an **existing public GitHub Release**
   `.cyclizer.plugin.zip` asset, and the archive's independently downloaded
   bytes must match `distribution.sha256`.
3. Source, archive and Catalog metadata must agree on publisher, capabilities,
   version, supported Host API and OS. Explicitly review any new capabilities.
4. Test the package against the current Host using an **isolated UserDataRoot**.
   Verify that installing a package does not silently activate it and that
   consent, enable/disable and safe detachment behave as expected.
5. Record the real download URI, source commit, digest, reviewer, review date
   and acceptance summary in the PR. Avoid copying secrets or personal data.
6. Change `revision` and `generated_at` for each approved new Catalog
   revision, and keep entry IDs deterministic/sorted. Once published, do not
   rewrite the bytes of a pinned Catalog commit or overwrite an existing
   Release asset.

## Removal or urgent disablement

An updated Catalog can stop advertising an entry but does not revoke already
installed packages and does not by itself stop a running Plugin. Host-side
revocation, trust policy and incident response are separate work. Never
describe Catalog removal as remote uninstall.

## Development Journal

The local `Workspace/cyclizer-plugin-development-journal` checkout is an
unpublished candidate. **Do not add it to `catalog/v1/index.json`** until its
separate source repository, actual authorized GitHub Release ZIP and digest,
and curator approval all exist. The Plugin reads the Cyclizer developer's
local `docs/plans` only; neither its package nor the Catalog may publish
those local plans or require a public documentation site. The bundled
Cyclizer `hello-*` examples are not automatically approved for publication.

## Hosting and pinning

The source-of-truth is `catalog/v1/index.json` at an immutable Git commit.
The future public location may use GitHub raw content delivery, such as:

`https://raw.githubusercontent.com/gsr-4325/cyclizer-plugin-catalog/<CATALOG_COMMIT_SHA>/catalog/v1/index.json`

`<CATALOG_COMMIT_SHA>` is a placeholder **only in this document**, never in
the published index. An immutable commit URL is used to obtain fixed JSON
bytes; its SHA-256 is independently calculated and supplied to Cyclizer's
explicit curator-import operation. This initial design requires no GitHub
Pages site, marketplace server, extra Plugin registry or automatic subscription
feature. Changes to the Catalog are not imported into users' running Hosts
merely by pushing to GitHub.
