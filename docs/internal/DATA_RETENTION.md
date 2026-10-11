# Data-retention and processing inventory

Internal draft, October 11, 2026; not an operational audit, adopted retention
schedule or guarantee of deletion. Proposed inventory owner: Matej Tokić,
acceptance pending. Read with [requests](GDPR_REQUESTS.md), [incidents](INCIDENT_RESPONSE.md)
and [routine verification](PRIVACY_SECURITY_CHECKLIST.md).

## Evidence boundary and actual architecture

**Source inspection** establishes implemented paths/defaults, not production
execution. **Operator-confirmed** facts establish the reported production/account
configuration, not an independent account/host inspection this session. **Unknown**
means confirmation is required. Verification methods below are future owner
actions, not commands already run. No environment files, provider attachments,
actual files/logs or private identifiers were inspected.

Evidence reviewed: [config.py](../../config.py), [storage](../../backend/services/storage.py),
[downloads](../../backend/services/downloads.py), [resource limits](../../backend/services/resource_limits.py),
[security helpers](../../backend/services/security.py), [HTTP downloads](../../backend/routers/downloads.py),
[main lifecycle](../../main.py), [MCP server](../../konvertira_mcp/server.py),
[MCP workflows](../../konvertira_mcp/tools/workflows.py), [MCP result orchestration](../../konvertira_mcp/tools/common.py),
[MCP store](../../konvertira_mcp/tools/image_metadata.py), [Office workspace](../../backend/processors/document.py),
[local images](../../frontend/src/services/localImageProcessor.ts),
[Compose](../../docker-compose.yml), [backend Dockerfile](../../backend/Dockerfile),
[frontend Dockerfile](../../frontend/Dockerfile) and [Nginx](../../frontend/nginx.conf).
Current public draft sources: [Privacy](../../frontend/src/legal/privacy.json),
[Terms](../../frontend/src/legal/terms.json), [Security](../../frontend/src/legal/security.json).

- Browser-labelled JPG/PNG/static WebP work stays local without upload fallback.
  PDF, Office, advanced image, background removal and all MCP operations are
  server-backed; common extensions can also use explicitly selected server tools.
- Most web workflows return bytes directly. MCP and compatibility paths can store
  generated results; no per-user account/file index or permanent archive exists.
- New results have a private bounded expiry sidecar binding creation/expiry to
  filename and file identity. Resolution and actual descriptor-backed response
  start independently deny expired results even if unlink fails. Startup and
  periodic cleanup recover space on `min(max(TTL/2,30),300)` seconds (300 by
  default), with safe expiry cleanup also attempted during resolution. Cleanup
  errors can leave physical files, not permission to download them. Legacy entries
  without metadata are unavailable and remain eligible for age-based cleanup.
  See [download security details](../storage-downloads.md) for clock, migration
  and already-started transmission limitations. This is local implementation
  evidence, not confirmation that production has deployed or exercised the fix.
- Results use random bearer tokens and mode 0600; possession of a URL gives access
  while available. Secure deletion/physical overwriting is not implemented.
- MCP retrieval validates HTTPS, standard port, no embedded credentials and
  allowed OpenAI host suffixes at every redirect with bounded bytes/timeouts. It
  receives selected references/parameters, not unrestricted ChatGPT history.
- MCP logs operational tool/outcome/duration/rejection information, not intended
  content or signed URLs. HTTP limiters use IP-derived short-window process state;
  inactive keys are removed opportunistically, not at an exact deletion deadline.
  Threaded work can continue after an MCP/background response timeout.
- Backend/MCP are separate non-root processes with dropped capabilities and
  no-new-privileges; the named bridge is not Docker internal-only isolation. The
  frontend is not claimed entirely non-root. These are source settings, not proof
  of all live privileges/host isolation.

## Inventory

| Category | Purpose and potential data | Location / role boundary | Confirmed configuration | Retention/deletion mechanism | Verification method (owner action) | Outstanding uncertainties |
| --- | --- | --- | --- | --- | --- | --- |
| Browser-local image operations | Pixel transformation; images, embedded information, preview/download | User browser/device; operator receives page requests, not selected local image bytes | Source: canvas decode/re-encode, JPG/PNG/static WebP, no upload fallback | Local buffers/object URLs released by browser/app; downloaded copies and device backups user-controlled | Harmless local fixture and browser network inspection; no image API upload | Browser/extensions/OS copies and user's backup retention outside operator control |
| Server uploads and in-memory processing | Requested conversion/inspection; file contents, filename, MIME, parameters, personal metadata | Backend/MCP memory; VPS hosting/HTTPS intermediaries can technically handle data | Source: bounded upload readers and decoders; OpenAI constrained download buffers; no general original-file archive | Normal request/job lifecycle, not stored-result TTL; no secure memory overwrite | Review route/processor lifetimes with harmless fixtures; inspect only relevant temporary locations | Multipart framework upload spooling may involve temporary disk files; effective spool locations, crash residue, swap/core dumps and proxy buffering not verified |
| LibreOffice workspaces | Office conversion; source, output and profile | Service temporary filesystem; operator/host controls | Source: random `konvertira-document-` TemporaryDirectory, separate profile, subprocess timeout default 60s | Context-manager cleanup on normal/handled exits; process/host failure can orphan files | Harmless success/failure test, bounded workspace metadata checks, ensure no active process before orphan removal | No demonstrated crash/orphan operational recovery, secure-media erasure or infrastructure-copy guarantee |
| Backend result volume | Temporary delivery; processed content and token filename | Compose `backend_results`, mounted `/tmp/konvertira-results` (configured mount, not private host address) | Source/default TTL 900s; result and expiry sidecar mode 0600; source capacity default 1 GiB; operator confirms dedicated volume | Persistent expiry/identity record; resolution and response-start deny expired access independently of unlink; startup/periodic cleanup recover space | Known harmless result, compare expiry/count/size before/after TTL and cleanup interval, verify download unavailable | Effective production TTL/quota, failure recovery, possible provider copies; no account-to-file mapping |
| MCP result volume | Temporary delivery to calling platform; output/report/ZIP | Compose `mcp_results`, mounted `/tmp/konvertira-mcp-results`; operator control, platform copies separate | Source/default TTL 900s; result and expiry sidecar mode 0600; source default quota 512 MiB; operator confirms dedicated volume | Separate store/lifecycle; persistent expiry enforced at delivery, physical deletion can fail | Harmless MCP result and expiry check; inspect bounded metadata without token/content exports | Active background jobs after timeout, orphan handling, OpenAI/recipient copies not deleted by expiry |
| Docker container logs | Operation/security diagnosis; timestamps, tool outcomes, possible request/diagnostic identifiers | VPS Docker logging, operator; frontend/backend/MCP/Caddy separate containers | Operator: json-file, max-size=10m, max-file=3 on all four; Caddy stack separate. Checked-in application Compose does not itself establish these overrides | Size-based rotation; **no fixed day retention**; exports separate | Narrow Docker inspect logging-driver/options fields for each actual container; inspect minimal time windows privately | Effective retention varies with traffic; actual fields/redaction/access and external exports |
| System journal | Host/service diagnostics; administrator/service events, technical identifiers | VPS systemd-journald, operator/host | Operator: SystemMaxUse=100M, MaxRetentionSec=14day; restarted/active | Journal-specific size/maximum-age controls, not other logs or exact-second erasure | Read effective journald settings, service state and disk usage in authorised host session | Other journal locations/exports/privileges, actual coverage and failure behaviour |
| Caddy request information | HTTPS origin routing/troubleshooting; possible IP/path/status/token information | Separate edge Compose stack on VPS; operator | Operator confirms Caddy json-file rotation 10m/3. Caddy config/access-log fields not present/verified here | Container stdout logs rotate by size; any separately configured access-log sink has its own policy | Inventory actual Caddy log sinks/fields/access and verify narrowly; do not print full config/secrets into issues | Access logging enabled/fields/sinks, token redaction and non-Docker retention unknown |
| Cloudflare request information | DNS/proxy/edge security/traffic analytics; IP, timestamp, hostname/path, method, status; HTTPS content handling | Cloudflare services; processor/independent roles depend on activity | Operator: HTTP request analytics/logs available; self-service DPA incorporated into applicable terms | Provider/account-specific mechanisms; no locally established universal period | Verify actual product/settings, accessible data and contract/retention documentation privately | Precise retention, access locations, transfers, subprocessors and role-specific rights assistance |
| Cloudflare Web Analytics/RUM | Browser audience/performance analytics if enabled | Cloudflare/user browser boundary | Operator: automatic injection disabled; frontend no Google/advertising analytics | Disabled feature is not proof of historical data deletion | Check current setting and harmless page responses/browser network behaviour | Historical analytics, manual scripts or live edge changes require review; disabling RUM does not disable technical logs |
| Cloudflare Logpush | Optional export of technical logs | Provider/export destination if enabled | Operator: not subscribed to or configured (inactive) | No configured Logpush export; does not erase provider request logs | Verify subscription and jobs/destinations without copying identifiers | Historical/export copies or other logging features not established |
| Contabo Auto Backup | Customer-facing VPS recovery feature if enabled | Contabo hosting; operator customer account | Operator: disabled; Contabo DPA concluded; VPS panel EU region | No enabled customer Auto Backup; **not proof of absence of provider-managed copies** | Verify panel state and relevant provider retention/recovery terms | Provider-level mechanisms, retention, access locations/transfers, exact data-center country unconfirmed |
| Contabo customer snapshots | Customer-created recovery copies | Contabo account | Operator: panel shows no customer snapshots | No shown customer snapshot to delete; distinguish infrastructure mechanisms | Confirm panel state, future creation and scope | Provider-managed recovery copies and historical deletions not established |
| Support/legal email | Enquiries, requests, complaints; sender/contact, message, attachments | Operator-selected email provider/mailboxes | Public addresses legal@konvertira.com and support@konvertira.com; no provider/schedule verified | Purpose-based owner schedule must be established; minimise attachments, sent/trash/export copies | Test delivery/monitoring with harmless messages; inventory provider and mailbox policies | Provider, access, retention, backup and transfer arrangements; no invented email deletion interval |
| GDPR request records | Accountability and responses; minimal contact/reference, decisions/actions | Private access-controlled store outside Git; store not yet selected/verified | This task drafts a blank register only, not a live implementation | Case-specific purpose/legal obligation/claims justification, review/deletion date; remove unnecessary verification material | Adopt storage/access/schedule, exercise synthetic request, review closure and deletion | Actual owner acceptance, location/security and legally justified duration unresolved |
| Incident records/evidence | Risk/notification decisions, investigation/remedies; minimal technical/personal facts | Private restricted store outside Git; incident evidence separately protected | This task drafts register/playbook only; no real incident/evidence included | Article 33(5) documentation where applicable; justified record/evidence review, narrow holds and deletion | Adopt safe evidence process, run synthetic tabletop, verify access and eventual deletion | Actual retention duration, absence cover, provider escalation and legal review unresolved |

## Request/incident record retention decision

Do not turn this inventory into a new permanent upload archive. At opening, the
owner must select private storage, allowed access, purpose/legal basis and a review
date. At closure, document any legal obligation, appropriate claims period or
continuing investigation supporting retention; choose a necessary proportionate
duration after legal review rather than inventing a universal number of years.
If undecided, schedule prompt reassessment with an explicit owner, not indefinite
retention. Separate a minimal decision record from shorter-lived ID material,
tokens and forensic evidence. Record holds and reassess them; remove unnecessary
copies and verify the available deletion mechanism, including mailbox exports.
Do not destroy legally required records, but do not preserve complete user files
merely to demonstrate accountability.

## Open questions and provenance

Contabo EU does not establish an exact country or EEA-only administrator/provider
access. Its DPA is concluded; Cloudflare's DPA is incorporated into applicable
standard self-service terms. Neither fact resolves every role or transfer.
No runtime download, training on uploads or external inference API is used for
background removal in the inspected code. PDF structure uses pypdf and rendering
pypdfium2/PDFium; [migration evidence](../pdf-processing.md) includes historical
local-only tests, while the [legal checklist](../legal-review-checklist.md) records
operator-confirmed subsequent Linux/production verification. That history does
not verify today's cleanup or all licences. Native/OS notices and broader
licensing review remain distinct from personal-data retention.

Inventory changes require owner review of actual settings and related disclosures,
not automatic changes to production. Unknown email/provider retention, transfers,
edge cookies, data-subject handling tests, registration/identity obligations and
final legal review stay open. Principles: [GDPR Articles 5 and 32](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng).
