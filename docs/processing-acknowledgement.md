# Website pre-processing acknowledgement

## Scope and implementation

The website now uses one native labelled checkbox immediately before each server
processing action. Its exact text confirms processing authority, server upload,
Terms acceptance and having read the Privacy Policy. The two same-site legal
links open separate tabs (announced to assistive technology) so reading them does
not discard the selected file or submit a request.

Shared component: `frontend/src/components/ProcessingAcknowledgement.tsx`.
Shared state/handler guard: `frontend/src/hooks/useProcessingAcknowledgement.ts`.
Every server component disables its processing action until accepted **and calls
the guard before any API call**. The guard returns false and exposes a concise
label-associated alert for unacknowledged handler invocation. Selection itself
never uploads. All processing buttons have type button, not implicit form submit.

Acceptance is component-local memory, bound to File object identities, ordered
file lists and the operation/options. Replacement selection explicitly resets it,
even for the same filename; changing operations/options resets synchronously
before submission becomes available. Returning to a prior operation cannot revive
acceptance. Errors do not authorize a replacement. Leaving/remounting the tool
starts unchecked. No storage, cookies, analytics, identity or acceptance records
were introduced.

The metadata tool uses action radios followed by one acknowledgement and one
processing button, avoiding duplicate checkboxes and acceptance transfer between
inspection and removal. Other tools keep their existing action layout.

## Complete website entry-point inventory

| Component / route | Guarded server operations |
| --- | --- |
| ServerImageConverter /convert | /images/convert, including explicit server common-image, HEIC/AVIF/static GIF, resize, quality and target-size options |
| BackgroundRemoval /convert | /images/remove-background, PNG/WebP |
| DocumentConverter /convert | /documents/convert for the existing supported document matrix |
| OfficeConverter /convert | /office/convert for existing spreadsheets and presentations |
| MetadataPrivacyTool /metadata | /metadata/inspect and /metadata/remove, separately selected actions |
| PdfToolkit /pdf-tools | /pdf/merge, extract, split, reorder, delete-pages, to-images, images-to-pdf, inspect-metadata, remove-metadata and optimize |

PDF merge and images-to-PDF bind acceptance to the whole selected list. Retries
use the same guard; changing files/operations/options requires fresh acceptance.
No website server-backed batch converter beyond those multiple-file PDF actions
exists. Unused compatibility helpers in api.ts are not mounted website entry
points; no other legacy uploading HTML/UI was found.

ToolCard (homepage and /convert) and BatchImageConverter (/convert) remain
browser-local, unchanged, without the server checkbox or upload fallback.
The website has no shared local/server mode toggle: these are explicitly separate
tools. Navigating between them does not carry acceptance.

Existing Terms/Privacy safeguards are consistent with the checkbox; their source
and generated content were left unchanged. The measure is contract transparency,
not universal GDPR consent, legal immunity, a rights waiver or API authentication.
Direct API clients and ChatGPT/MCP do not acquire a new web-session requirement.
Backend processing/security, TTL, MCP instructions, annotations and schemas remain
unchanged. No server-backed website entry point was left uncovered.

## Local validation

- npm test: **74 passed, 9 test files passed**, including actual component handlers,
  bypassing disabled controls, real mocked-fetch API requests, all ten PDF actions,
  both metadata actions, multiple files, errors and scope resets.
- npm run typecheck: passed.
- npm run build: passed (TypeScript and Vite).
- npm run legal:check: passed; no legal-source changes.
- Real-browser integration: **23 cases passed**, headless Microsoft Edge with
  existing bundled Playwright; native keyboard checkbox/action, disabled handler
  bypass, server drag/drop with no upload, actual local image drag/drop and canvas
  processing, local batch, legal-link file preservation and 320/390/1280 px layouts.
  All processing traffic mocked; no production uploads/settings changed.
- Project venv Python: **3 MCP schema/registration tests passed**, checking all 16
  names/annotations and OpenAIFile/PDF schemas.
- git diff --check: passed (only Git LF/CRLF conversion warnings).
- Git diff confirmed no backend/MCP/API/configuration, dependency, local processor
  or legal-source changes. No actual user content, credentials or private records
  were added; browser fixtures are generated harmless test data.

Browser checks can be repeated from frontend with an existing Playwright install:

```powershell
node scripts/check-processing-acknowledgement.mjs 'ABSOLUTE_PATH_TO_PLAYWRIGHT_PACKAGE'
```

The script starts a loopback-only Vite instance, intercepts all API traffic, and
closes its browser/server. Default browser channel is msedge; ACK_BROWSER_CHANNEL
can select another installed Playwright-compatible channel. No new project
dependency is required.

## Suggested deployment (not executed)

After developer review, use the existing production Compose environment/build
arguments so VITE_API_BASE_URL remains correct:

```sh
docker compose build frontend
docker compose up -d --no-deps frontend
```

These target only the frontend; do not rebuild/restart backend, MCP or Caddy or
remove volumes. Smoke-check /convert, /pdf-tools and /metadata with harmless files:
zero upload before acknowledgement, reset on replacement/operation change and
successful accepted processing. Confirm homepage/local batch remain local and
legal links work. This UI change does not resolve the existing final legal-review
gates. No commit, push, deployment, restart or plugin submission was performed.

## Files changed

- frontend/src/components/BackgroundRemoval.tsx
- frontend/src/components/DocumentConverter.tsx
- frontend/src/components/MetadataPrivacyTool.tsx
- frontend/src/components/OfficeConverter.tsx
- frontend/src/components/PdfToolkit.tsx
- frontend/src/components/ServerImageConverter.tsx
- frontend/src/components/ProcessingAcknowledgement.tsx
- frontend/src/components/ProcessingAcknowledgement.test.tsx
- frontend/src/hooks/useProcessingAcknowledgement.ts
- frontend/scripts/check-processing-acknowledgement.mjs
- docs/processing-acknowledgement.md
