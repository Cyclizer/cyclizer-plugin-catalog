## Plugin listing change

Describe the Plugin, publisher, exact version and why it should be discoverable.
If this is a policy or tooling change without a listing, explain that instead.

## Verification evidence (required for each new or changed listing)

- [ ] Plugin source repository and **exact source commit SHA** inspected
- [ ] Public GitHub Release asset exists and can be anonymously downloaded over HTTPS
- [ ] Downloaded `.cyclizer.plugin.zip` bytes match the listed SHA-256
- [ ] Package Manifest v2 IDs, publisher, version, requested capabilities and supported Host API/OS match the Catalog entry
- [ ] Plugin code, license, provenance and permissions reviewed by the Catalog curator
- [ ] Installation/activation tested in an **isolated** Cyclizer Host/UserDataRoot, without touching the operator's usual instance
- [ ] `python scripts/validate_catalog.py` and `python -m unittest discover -s tests -v` pass
- [ ] Curator explicitly approves discoverability; this does **not** grant execution permission

**Evidence:** Add immutable source/release URLs, artifact SHA-256 and a short test summary.
Do not add an entry with a speculative Release URL or placeholder hash.
