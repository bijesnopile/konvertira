# Stored-result expiry and descriptor-backed downloads

Local implementation, October 11, 2026. Not deployed by this task. This report
separates application access denial from physical deletion and provider retention.

## Root cause and complete path inventory

Previously `TemporaryStorage.resolve()` returned any matching regular-looking
path without checking TTL. Download handlers ran cleanup first, but cleanup
ignored unlink/stat errors. An expired file could therefore still be returned.
Starlette FileResponse later reopened the path, leaving another check/open race.

Both stores now share the same enforcement:

- Backend `api_storage`: configured result directory, default TTL 900 seconds,
  quota from `MAX_TEMP_STORAGE_BYTES`; Compose backend result volume.
- MCP `mcp_storage`: separate configured directory and quota from
  `MCP_MAX_TEMP_STORAGE_MB`, same configured TTL; separate MCP result volume.
- `backend/services/image_workflow.py` creates stored image results through
  `clean_and_store`; legacy metadata actions in `backend/routers/metadata.py`
  reuse that service and return the unchanged `/download/{token}` URL.
- `konvertira_mcp/tools/image_metadata.py` uses its store; all conversion/PDF/
  metadata workflows use `konvertira_mcp/tools/common.py` result orchestration.
  Metadata reports returned inline are not turned into a new permanent archive.
- Backend `backend/routers/downloads.py` and MCP `konvertira_mcp/server.py` are
  the only token file-serving routes found; both use the shared late-open response.
- `main.py` and MCP lifespans independently run startup and periodic cleanup;
  `backend/compat.py::cleanup_old_files` still delegates to the backend store.
  `resolve()` remains a compatibility API but now checks expiry and identity;
  it is not permission to later reopen a path for serving.
- `backend/services/downloads.py` is the constrained **input** OpenAI downloader,
  not a result-serving boundary; its host/redirect/size/time controls are unchanged.
  Direct-response conversion routes are not persistent-token download paths.

## Expiry authority, restart and migration

Each new result has a private `.TOKEN.json` sidecar with controlled filename,
creation/absolute expiry and device/inode/size/mtime identity. It contains no user
profile or original filename. It is at most 1024 bytes when read, stored mode 0600
alongside a mode-0600 result and charged to the same storage capacity. Results
are returned to callers only after the record is written; a failed save is denied
and partial owned entries are safely removed where possible. There is no database
or new dependency. Failed deletion remains charged to capacity until removed.

An entry expires when current time is **at or beyond** the earlier of its issued
expiry and creation plus current configured TTL. Lower TTL overrides shorten
existing access; increasing TTL applies to new results and cannot renew existing
issued tokens. Downloads neither touch mtime nor extend expiry. Persistent records
survive a process restart and prevent touching/replacing an output from creating
a new legitimate lifetime. Missing, invalid, oversized or mismatched records fail
closed with the existing 404 response, not file bytes or host paths.

**Migration choice:** pre-fix results lack trustworthy persistent authority and
are denied, even if their mtime appears fresh. This intentionally invalidates
short-lived old links on rollout; users can regenerate results. Old generated
entries remain eligible for bounded age-based physical cleanup. Do not fabricate
new timestamps or migrate old entries into renewed access. Dangling sidecars and
crash residue can be reclaimed by cleanup; unrecognised filenames/symlinks are
not traversed or blanket-deleted.

## Actual serving boundary and races

The shared response validates and safely opens at ASGI response execution, checks
expiry after open and immediately before response start, then streams 64 KiB
chunks from that same descriptor. Result/record symlinks, reparse entries,
non-regular files, multiply linked files and changed file/directory identities
are denied. POSIX open/create/unlink use a pinned directory descriptor and
no-follow flags. Windows uses lstat/reparse and identity checks; it lacks identical
POSIX dir-fd semantics. Linux-specific behaviour still needs execution there.

Deletion before opening returns 404. Replacement after opening cannot redirect
the descriptor to another file; on Windows deletion may instead be blocked by
the open handle. Normal completion, client disconnect, cancellation and read/send
errors close descriptors in a finally block. Filesystem operations use existing
AnyIO worker support without abandoning a cancelled descriptor-opening/read job.
An actual device/read error after headers can interrupt a stream; it cannot turn
it into a new successful replacement-file response.

Successful/error downloads retain no-store and nosniff. Safe attachment filenames
and registry-derived MIME types are unchanged, including ZIP/Office outputs.
Rate-limit responses retain Retry-After. Full attachment streaming is bounded
and does not load the entire result; Range is not advertised/implemented by the
new response, so clients receive a full 200 attachment rather than resumable
FileResponse ranges. No ETag/Last-Modified caching policy is added.

## Cleanup, clocks and explicit limits

Startup cleanup and the independent periodic tasks remain the primary space
recovery mechanism. Expired resolution also attempts narrow removal; denial
does not depend on either result or record unlink succeeding. Cleanup retries
remaining generated entries, uses record expiry where available, retains the
per-store write lock, and continues after recoverable filesystem errors. Default
periodic interval remains 300 seconds, bounded 30–300. Minimal diagnostics use
fixed reason labels, throttled per reason, not tokens, paths, signed URLs or content.

The per-store time floor advances with monotonic elapsed time and wall time, so
backwards wall-clock adjustment cannot renew access within a running process.
Absolute persisted expiry necessarily relies on a reasonably correct host clock
across restart. If the clock is rolled back across restart into an old lifetime
and both deletion attempts previously failed, no trusted external clock/persistent
anti-rollback service exists to establish the true elapsed time. A forward jump
can expire results early. Maintain host time; this is not cryptographic expiry
against a compromised administrator or arbitrary storage/sidecar tampering.
Identity checks also are not cryptographic integrity protection against an actor
able to rewrite files and their metadata as the service owner/root.

A delivery admitted while valid may **finish after TTL** on its pinned descriptor.
It is not mid-stream revocation or recall of bytes already sent, buffered or
downloaded. A new request is denied after expiry. This behaviour is covered by
tests. Per-process write locks do not implement distributed coordination; preserve
the documented single-worker-per-store baseline and do not share a store between
concurrent independent writers without additional review.

Deleting a file does not erase browser/OpenAI copies, edge/provider caches,
snapshots, logs or media. Docker size rotation and journald rules are unchanged.
Unlink failures may fill capacity and need private operational investigation;
application access denial does not prove physical cleanup, input-workspace cleanup
or GDPR compliance. See [retention inventory](internal/DATA_RETENTION.md),
[incident procedure](internal/INCIDENT_RESPONSE.md) and [legal gates](legal-review-checklist.md).

## Exact files changed for this fix

- `backend/services/storage.py`
- `backend/services/result_downloads.py` (new)
- `backend/routers/downloads.py`
- `konvertira_mcp/server.py` (download handling/headers only)
- `main.py` (download error cache headers only)
- `tests/backend/test_storage.py`
- `tests/backend/test_result_downloads.py` (new)
- `tests/mcp/test_image_metadata_tool.py`
- `tests/mcp/test_workflows.py` (exclude sidecars from output fixtures/counts)
- `docs/internal/DATA_RETENTION.md`
- `docs/internal/GDPR_REQUESTS.md`
- `docs/internal/INCIDENT_RESPONSE.md`
- `docs/legal-review-checklist.md`
- `docs/storage-downloads.md` (new)

All 16 MCP registration names, descriptions, annotations and schemas are unchanged;
the existing registration/OpenAIFile regression tests run with the full suite.
No processors, quotas/timeouts, registry, host allowlists, dependencies, production
configuration or public legal source/generated HTML changed for this fix. Earlier
uncommitted legal-page edits and internal procedure drafts were preserved.

## Local validation and recommended deployment review

Run from repository root (no production files or provider requests in these tests):

```powershell
.\venv\Scripts\python.exe -m pytest -q -ra
.\venv\Scripts\python.exe -m pytest tests/backend/test_storage.py tests/backend/test_result_downloads.py tests/backend/test_pdf_api.py tests/mcp -q
.\venv\Scripts\python.exe -m compileall -q main.py mcp_server.py config.py backend konvertira_mcp scripts
.\venv\Scripts\python.exe -m pip check
git diff --check
```

Tests use real isolated files/stores and HTTP routes, deterministic clocks and
selective injected filesystem failures. Coverage includes failed unlink with
remaining bytes/404, restart, overrides, legacy entries, no TTL refresh, path/token
validation, malformed sidecars, output identity, symlink/hard-link protections,
concurrent cleanup, late opening/expiry, disconnected/cancelled/read-error closure,
already-started transmission, storage quotas, MIME/attachments and cache headers.
Symlink/POSIX permission tests can be skipped on Windows; they must be run on Linux.

Docker daemon was unavailable locally (dockerDesktopLinuxEngine pipe missing);
no image build or Linux runtime smoke test ran. Python tests/compilation/pip checks
completed with these actual results:

- Full pytest: **246 passed, 5 skipped, 6 existing pypdf deprecation warnings**.
- Targeted storage/download/backend PDF API/MCP run: **130 passed, 3 skipped,
  4 existing pypdf warnings**.
- Full-suite skips: opt-in real background inference, unavailable local
  LibreOffice, two symlink cases unavailable without Windows symlink privilege,
  and POSIX private-mode test on Windows. These are not Linux passes.
- `compileall`, `pip check` and `git diff --check`: passed; diff check only emitted
  Git LF/CRLF conversion warnings.
- Documentation local-path check: **47 links resolved**.

Frontend checks are unnecessary for this
fix because no frontend files changed during it.

Before a separately authorised rollout:

1. Review patch and migration: old token links will return 404. Preserve existing
   hardening; do not back up actual transient user volumes merely for this change.
2. On an isolated Docker-capable Linux host, build the shared backend image without
   recreating production services. Run the storage/download regressions with tests
   supplied to a disposable container, no production result volumes or secrets;
   verify symlink/permission tests execute instead of skipping. Model build steps
   can require the existing fixed model download; do not add runtime downloads.
3. Only after deployment is independently approved, update both backend and MCP.
   Use harmless web legacy/MCP results to check immediate successful downloads,
   MIME/attachment/no-store/nosniff, 404 after the effective TTL, restart behaviour
   and old-link denial. Verify health **and** real file workflows and the 16 tools.
4. Test unlink-denied behaviour only in isolated storage/container fixtures, not
   by changing production volume permissions. Check actual periodic cleanup,
   bounded disk growth and private diagnostics; investigate remaining residue.
5. Separately review public wording locations recorded in the legal checklist;
   do not silently regenerate/publish legal pages with this security change.

No commit, push, merge, deployment, production restart or publication performed.
