# GitHub-hosted catalog test retirement

## Owner decision (2026-10-29)

The owner requested the shutdown of automatic GitHub Actions tests across the
Workspace's repositories. The Catalog previously registered
`.github/workflows/validate-catalog.yml` for pull requests, pushes to `main`,
and manual dispatch. Retiring that file prevents these triggers from being
defined by future `main` revisions. This does not retroactively cancel an
already queued/running GitHub Actions job or necessarily mark a workflow as
`disabled_manually` in GitHub's Actions API.

## Verification still required

The schema and catalog-policy validator and regression tests remain in the
repository. For future catalog changes, use an AI-owned isolated environment
or another explicitly authorized verification runtime. Run
`python scripts/validate_catalog.py` and
`python -m unittest discover -s tests -v`, record the exact source revision,
environment, results and limitations, and retain explicit curator approval.
Do not run unapproved broad tests on the owner's Windows machine. The absence
of CI, or a deleted required status check, is **not** evidence of test PASS.
If branch protection requires a now-deleted check, an authorized repository
administrator must reconcile that rule before merging affected PRs.

## Scope, state and restoration

- Retired workflow: `validate-catalog.yml`, baseline `main` at
  `52eaeee9bfab856fe2b0140bec03153290679dd1`.
- Application source, catalog index, schema, tests and plugin acceptance
  policy are unchanged. No release, notification, or security workflow is
  removed.
- The old workflow can be recovered from Git history with
  `git show 52eaeee9bfab856fe2b0140bec03153290679dd1:.github/workflows/validate-catalog.yml`,
  then restored through a separately reviewed PR.
- Verify the merged PR and remote `main` readback before claiming shutdown.
  Separately check the Actions API/UI for retained workflow registrations
  and running jobs; stop them only with appropriate permissions.
- This documentation/workflow removal did **not run** hosted or local tests.
