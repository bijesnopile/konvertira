# Konvertira legal/privacy/security pre-publication review

Review date: October 11, 2026. **Local draft only; do not publish these pages as
legally complete until the blockers below are resolved.** This is an engineering
evidence record and review checklist, not a legal opinion or GDPR/licence audit.
An unchecked item is unknown or unconfirmed, not a negative answer.

## Verified and completed — final disclosure update

Evidence boundary: production/account facts below were expressly confirmed by
the operator in the final documentation task on October 11, 2026. They are not
represented as fresh remote checks performed during this local editing session.
Repository-backed processing facts were checked against current source. No
private account identifiers, environment values or server credentials were read.

- [x] Operator: Matej Tokić, independent natural person based in Croatia, not
  currently operating through a registered company or trade. This factual status
  does not settle legally mandatory disclosures or registration obligations.
- [x] Currently no subscriptions, advertising, paid credits, checkout or other
  implemented monetisation; no promise of permanent free availability.
- [x] Contabo hosting and concluded DPA; VPS panel location EU. The exact
  data-center country was not independently established.
- [x] Contabo Auto Backup disabled; no customer snapshots shown. This is not
  proof that provider-operated infrastructure copies do not exist.
- [x] Cloudflare DNS, reverse proxy/HTTPS and edge/network services in use;
  DPA incorporated into applicable standard self-service terms.
- [x] Cloudflare automatic Web Analytics/RUM injection disabled; Logpush neither
  subscribed to nor configured. HTTP request analytics/logs remain available,
  including IP, timestamp, hostname/path, method and response status.
- [x] Docker json-file rotation applied to frontend, backend, MCP and Caddy:
  max-size 10m, max-file 3 per service. Size-based, not fixed time retention;
  application services and Caddy use separate Compose stacks.
- [x] systemd-journald SystemMaxUse=100M, MaxRetentionSec=14day; restarted and
  active. Applies only to the system journal, not a universal log schedule.
- [x] Two dedicated result Docker volumes; default result TTL 900 seconds,
  periodic/request cleanup with failure and orphan caveats verified in source.
- [x] PyMuPDF removed from new production backend/MCP images; pypdf 6.20.0 and
  pypdfium2 5.14.0/PDFium retained. PDFium rendering verified on Contabo Linux;
  all 16 public MCP tools verified after deployment (operator confirmation).
- [x] Public checks after logging changes: https://konvertira.com/ HTTP 200,
  https://api.konvertira.com/health healthy and
  https://mcp.konvertira.com/health healthy (operator confirmation).

## Still requires confirmation — publication gates

- [ ] Legally required operator identification, lawful contact/postal/service
  address and applicable disclosure requirements for the actual Croatian natural
  person. No private address or invented identifiers have been published.
- [ ] Applicability of business/trade registration, trader status, consumer and
  e-commerce obligations even for a currently free service.
- [ ] Final Croatian/EU-qualified legal review, including lawful bases and roles,
  consumer safeguards, liability wording and language/accessibility requirements.
- [ ] Contabo/Cloudflare provider-level retention, precise contracting entities,
  provider access locations and relevant international-transfer mechanisms;
  exact VPS data-center country if legally relevant. DPAs are not proof that all
  transfers/access or every provider activity have been fully assessed.
- [ ] Email-specific retention, contractual roles/agreements, access locations,
  transfers and mailbox monitoring/absence arrangements; routing/delivery confirmed.
- [ ] Cookie behaviour at the live edge in returning sessions, challenges and
  other routes, and any required ePrivacy disclosures; one fresh homepage
  incognito inspection had an empty cookie table, not a never-cookies finding.
- [ ] Practical data-subject request and incident-response procedures.
- [ ] Complete third-party licensing review for shipped wheels, native/OS
  components and historical images, including GCC Runtime Library Exception
  conditions. Former PyMuPDF runtime blocker is remediated, not the entire audit.

Detailed open assessments below remain applicable. Confirmed items must not be
reopened as wholly unknown, nor used to mark broader legal questions complete.

## Latest operator confirmations — email, cookies and deployed expiry fix

- [x] Both public addresses manually tested: sender → Cloudflare Email Routing
  → Google Gmail; incoming delivery succeeded. Retention, contractual roles,
  Google agreement status and transfers are not verified; no separate Google DPA asserted.
- [x] Fresh Chrome incognito homepage: DevTools Application → Cookies for
  https://konvertira.com showed an empty table during inspection. Other conditions
  may involve necessary Cloudflare security/challenge cookies.
- [x] Updated backend and MCP deployed on Contabo; operator reports **92 Linux
  storage/download tests passed** and **41 Linux backend PDF API/MCP tests passed**.
  Both public health endpoints returned HTTP 200; metadata inspection/removal
  succeeded. Harmless MCP result: HTTP 200 before expiry, HTTP 404 afterwards.
  Automated tests cover expiry denial when physical unlink fails. These are
  operator confirmations, not remote tests performed in this editing session.

## Internal procedures — drafted, not operationally verified

Deployed expired-download fix (operator-confirmed): token resolution and actual descriptor-backed delivery
now check persistent expiry metadata independently of physical unlink. Startup
and periodic cleanup remain space recovery, not the access security boundary.
Legacy results without the new record are denied. See
[storage/download implementation and limits](storage-downloads.md).
This does not verify production cleanup, change provider/log retention, settle
legal gates or mean the internal procedures have been operationally tested.

Public copy updated locally: Privacy temporary storage/retention table, Terms
storage and Security results/logging now separate persisted expiry/access denial
from physical cleanup. Already-started valid downloads may finish; provider,
browser, OpenAI and recipient copies are separate. Static HTML regenerated from
the same source as React; this is not a frontend publication.

Five internal templates were drafted on October 11, 2026:
[GDPR requests](internal/GDPR_REQUESTS.md),
[incident response](internal/INCIDENT_RESPONSE.md),
[retention inventory](internal/DATA_RETENTION.md),
[routine checklist](internal/PRIVACY_SECURITY_CHECKLIST.md) and
[response templates](internal/RESPONSE_TEMPLATES.md).
They contain no actual cases, secrets or private provider attachments; completed
registers/evidence must be stored privately outside Git and public web roots.

| Milestone | Status | Remaining evidence/action |
| --- | --- | --- |
| Procedure documented | Drafted only | Review against actual operations and contracts |
| Procedure tested | Not tested | Synthetic rights-request and incident tabletop exercises |
| Responsibility assigned | Not formally assigned/accepted | Matej Tokić is proposed owner; confirm mailbox habits, access and absence cover |
| Legal review completed | Not completed | Roles, deadlines, exceptions, notification decisions and justified record retention |

The open practical-request/incident procedure item above remains unchecked.
Markdown/source consistency checks do not establish operational execution.
Operator identification/address, registration, consumer duties, provider-level
retention, transfers and broader licensing gates remain unresolved and unchanged.

## Release blockers and controller identity

Public identification is limited to Matej Tokić, Croatian independent-natural-person
status, Konvertira and public legal/support contacts. No private address, OIB/VAT,
business identifier, phone or invented company may be added. These minimal facts
do not necessarily satisfy Croatian/EU disclosure obligations. Qualified review
must resolve required identification, lawful contact/service address, registration
and complaint duties before treating publication as legally complete.

- [ ] Obtain Croatian/EU-qualified legal review of all three original English
  drafts, especially controller roles, consumer remedies and Terms section 22's
  narrowly qualified non-consumer loss exclusion. No numerical liability cap,
  mandatory arbitration, class-action waiver or consumer indemnity was added.
- [x] Confirm Matej Tokić is the operator, an independent Croatian natural
  person without a registered company/trade for this project. Applicable legal
  capacity, controller roles and any required registration remain for review.
- [ ] **PRE-PUBLICATION LEGAL REQUIREMENT:** provide a lawful postal/service
  address and all legally required controller/operator contact information.
  No private address was searched for or copied into this repository. Do not
  assume an email address alone satisfies applicable information duties.
- [ ] Determine whether a registered trade/company identity, business register,
  OIB/VAT identifier, telephone number or further Croatian e-commerce/operator
  disclosure must be displayed for the actual operator. Do not invent them.
- [x] Operator manually verified incoming delivery to Gmail for both public addresses.
- [ ] Verify monitored mailbox access, checking habits and absence coverage.
- [ ] Determine whether a GDPR DPO is required (Article 37). Do not invent an
  appointment. Determine Article 27 representative applicability; a Croatia-based
  establishment ordinarily presents a different question from a non-EU operator,
  but actual establishment and any exceptions must be assessed.
- [ ] Resolve remaining provider-level retention, access and transfer disclosures.
  Hosting, applicable DPAs, logging and incoming email routing are confirmed.
  Public notices retain substantive limits; unresolved legal identification stays
  in this checklist. Final-document styling does not establish legal completeness.
- [ ] Set the real effective/publication dates and any required change notice or
  record of the previous policies. Current dates are labelled Last updated for local copy,
  not a representation of a completed production rollout.

## Code-backed facts reviewed

| Area | Evidence | Draft treatment |
| --- | --- | --- |
| Local image operations | `frontend/src/services/localImageProcessor.ts`, its tests, `format_registry.json` | Browser canvas JPG/PNG/static WebP; no upload fallback. A server tool for the same extension remains server-side. |
| Server and MCP operations | `backend/routers/`, `backend/processors/`, `konvertira_mcp/server.py`, `konvertira_mcp/tools/` | Shared processors, actual supported matrix; no audio/video or account/checkout system. |
| MCP inputs/results | `konvertira_mcp/models/files.py`, workflows, `backend/services/downloads.py` | Selected OpenAI file reference/parameters; no unrestricted conversation access. Metadata reports can themselves reveal personal data. |
| Stored results | `backend/services/storage.py`, download routes, `config.py` | Default 900-second result TTL; periodic 30–300-second cleanup, request-triggered cleanup, filesystem-error/outage caveats. No all-system or exact-second erasure claim. |
| Input/intermediate files | `backend/processors/document.py`, background router | Memory buffers; LibreOffice temporary workspace/profile with normal cleanup. Result TTL is not an input-retention guarantee. |
| Quotas/timeouts | `backend/services/rate_limit.py`, `resource_limits.py`, `config.py` | Per-process HTTP limits, global MCP gates, retained capacity for continuing work; no claim every HTTP job can be killed at a fixed deadline. |
| Logging | `resource_limits.py`, Docker commands, Nginx; operator-confirmed production settings above | MCP operational logs; Docker size rotation and journald rules have distinct scopes; Cloudflare request logs exist, provider periods unknown. |
| Packages | `backend/services/metadata.py` | Bounded metadata archive parsing, encrypted/traversal checks, hardened XML; not a universal safety guarantee for all engines. |
| Runtime | `docker-compose.yml`, both Dockerfiles | Non-root backend/MCP, dropped capabilities, no-new-privileges, loopback bindings and named volumes. The network named internal is a bridge, not `internal: true`. Frontend is not claimed non-root. No read-only rootfs/cgroup budgets asserted. |
| Background removal | Processor, preparation/permission scripts, `docs/background-removal.md`, bundled Apache licence | U²-NetP, fixed URL/hash, CPU ONNX session, default one inference thread, no runtime download or external inference API, no training on uploads. |
| Browser tracking | `frontend/src/`, public assets and Nginx inspection; operator confirmation | No frontend Google/advertising analytics or persistent user profiles. Cloudflare RUM disabled; request analytics/logs still available. One fresh homepage incognito table was empty; other scenarios remain unverified. |

The requested `docker-compose.prod.yml` does **not** exist in this checkout;
`docker-compose.yml` is the available source. No Caddy configuration or domain
challenge/MCP rewrite was changed. Deployment assumptions are not converted into
facts by a hostname, documentation recommendation or provider brand.

## Processing roles and lawful bases

- [ ] Record controller/processor roles by data flow, including organisational
  users' files, other people's data inside uploads, OpenAI and each provider.
  The operator is described as controller for his own operational processing,
  not automatically controller or processor of every possible uploaded dataset.
- [ ] Assess contractual necessity under Article 6(1)(b) for the requester's data.
  A contract with the sender is not automatically a basis for all third-party
  content. Assess Article 14 information duties and lawful exceptions separately.
- [ ] Document legitimate-interest necessity/balancing for security, troubleshooting
  and general correspondence, including objection handling. Identify actual
  legal obligations for Article 6(1)(c), rather than using it as a catch-all.
- [ ] Do not introduce consent by browsing/accepting Terms. If an optional feature
  uses consent, implement valid choice, evidence and withdrawal for that purpose.
- [ ] Determine Article 9/10 conditions if any specially protected content is
  accepted. Consider whether restricting inappropriate sensitive uploads is
  necessary; an ordinary contract cannot resolve special-category requirements.
- [ ] Obtain required Article 28 agreements and documented instructions. The
  public interface does not currently supply a negotiated enterprise DPA.
- [ ] Consider a processing record (Article 30), risk assessment, DPIA triggers,
  children's data/capacity rules and the actual audience; a small operator does
  not receive a blanket exemption from substantive duties.
- [ ] Confirm no submitted-content training, sale or profiling has been introduced
  outside the inspected implementation. OpenAI handling remains independent.

## Providers, jurisdictions and transfers

- [x] Confirm Cloudflare DNS and reverse proxy/HTTPS traffic handling; RUM
  disabled and Logpush inactive. Exact contracting entity, subprocessors,
  access/data locations and other account features remain to be documented.
- [x] Confirm Contabo hosting, EU panel region, concluded DPA and customer-facing
  backup/snapshot state. Contracting entity, support/admin-access territories,
  exact country and provider-level recovery/retention remain to be established.
- [ ] Complete provider inventory/role review for confirmed Cloudflare Email
  Routing → Google Gmail, DNS, proxy, monitoring, logging and other providers.
  Distinguish code dependencies from hosted services receiving personal data.
- [ ] Review provider contracts/DPA terms, controller/processor roles and
  subprocessors. Do not classify every third party automatically as a processor.
- [ ] Map OpenAI file download and returned-results flows separately from the
  user's ChatGPT account relationship; verify relevant current platform terms.
- [ ] Identify transfers/remote access outside the EEA, including CDN, email,
  vendor support and calling platform. Do not claim EEA-only processing.
- [ ] Document each applicable adequacy/safeguard mechanism, supplementary measures
  and transfer assessment under Articles 44–49. No SCCs, adequacy arrangement or
  consent derogation is asserted as operational without evidence.
- [ ] Explain how people can obtain safeguard information/copies with appropriate
  redaction. Add verified recipient and territory disclosures to the notice.

## Retention, logs and backups

- [ ] Verify effective production TTL and actual cleanup operation on both stores;
  disclose materially different settings, errors, outage and orphan handling.
- [ ] Inspect reverse-proxy/CDN/browser-cache behaviour for uploaded and generated
  content, not just application `no-store` responses.
- [ ] Specify application, MCP, Nginx, external proxy, container/host, security and
  provider log fields, access permissions, rotation and maximum retention.
  Audit whether paths contain download tokens or signed URLs; establish redaction.
- [ ] Establish mailbox, rights-request, complaint and incident-record retention
  schedules tied to purpose and specific legal obligations/claim periods.
- [x] Check customer-facing VPS backup/snapshot state: Auto Backup disabled and
  no customer snapshots shown. Provider infrastructure mechanisms and historical
  copies are not ruled out; their retention/deletion and restore practices remain
  for review, including any future named-volume backup policy.
- [ ] Test normal workspace cleanup and crashed-job/orphan recovery without
  promising cryptographic erasure or overwriting of provider media.
- [ ] Review who can access processing files/logs and when operational access is
  justified. Do not promise audited role-based administration if not implemented.

## Cookies and production security

- [x] Operator inspected fresh Chrome incognito homepage cookies: empty table.
- [ ] Inspect returning sessions, other routes and security/challenge responses,
  including any Cloudflare cookies or injected analytics.
- [ ] Determine applicable ePrivacy/Croatian terminal-storage requirements; provide
  disclosures and prior choice for non-essential tracking where required. The
  absence of frontend trackers does not prove an edge provider sets no cookies.
- [ ] Verify TLS, termination points, HSTS suitability, CORS/proxy trust,
  origin access restrictions and coarse edge limits; keep existing CSP/headers.
- [ ] Confirm one worker per backend/MCP service or equivalent coordinated limits.
  Inspect production memory/CPU budgets and egress protections; none are invented
  by these documents. Do not expose a Docker socket or broaden host mounts.
- [ ] Document patch/dependency review, access controls and model integrity checks.
  Keep model/licence/attribution root-owned and read-only to runtime users.
- [ ] Set a vulnerability-reporting and escalation process for the actual monitored
  contact channel. No bug bounty, external audit, certification or 24/7 SOC exists
  as a verified repository fact.

## Rights requests and incident procedure

- [ ] Implement a practical rights-request register, proportionate verification,
  record location, response templates, recipient notification and escalation.
  Respect one-month replies and lawful extension rules; do not request unnecessary
  ID or reconstruct deleted history solely to identify someone.
- [ ] Confirm access, correction, erasure, restriction, objection and applicable
  portability/consent-withdrawal handling, including other people's rights.
- [ ] Provide accurate AZOP/other authority complaint information; never imply
  authority endorsement or require users to contact the operator first.
- [ ] Document breach detection, containment, evidence minimisation, risk assessment
  and the relevant Article 33/34 notifications. Establish who receives provider
  incident notices and can act during absence; no response-time guarantee invented.
- [ ] Distinguish file transformations/rate checks from Article 22 legally or
  similarly significant individual decision-making; reassess if features change.

## Consumer and contract review

- [ ] Assess whether the operator is acting as a trader and which consumer and
  e-commerce information duties apply, including free digital-service scenarios.
- [ ] Review acceptance/presentation before processing; an accessible policy link
  alone is not a legal opinion on contract formation. No checkbox/API change was
  added here. Assess any required durable-medium notices and withdrawal remedies.
- [ ] Review mandatory conformity, security-update, modification and remedy rules,
  applicable Croatian written complaints (including acknowledgement/15-day reply
  duties), required records and complaint channels.
- [ ] Review reasonable suspension grounds, change notices, capacity/age rules and
  governing law without displacing consumer residence/jurisdiction protections.
- [ ] Validate civil-obligations carve-outs for intent, gross negligence and other
  non-excludable liability. File/back-up cautions must not become a release from
  operator duties or a blanket exclusion for all loss of data.
- [ ] Check applicable Croatian-language/accessibility requirements for this
  English-language release. Do not infer that English alone is sufficient for
  every domestic consumer-information obligation.

## Licensing and notices — non-exhaustive review, not an audit

- [x] PDF renderer migration: PyMuPDF removed from runtime requirements and local
  test environment; pypdf 6.20.0 remains for structure, pypdfium2 5.14.0/PDFium
  replaces rasterisation. The project's `All rights reserved` licence is unchanged.
  New production images no longer install it; PDFium rendering and all 16 MCP
  tools were verified on the Linux deployment according to the operator.
  See `docs/pdf-processing.md` for migration evidence and retained notices. Its
  earlier local Docker-unavailable record is historical, not a production claim.
- [ ] Review third-party redistribution notices for the actual shipped PDF wheel.
  BSD/Apache/MIT and native component notices are retained; the shared Dockerfile
  collects all installed PDF distribution licence files. This removes the former
  renderer dependency, not every possible licensing obligation. Historical copies
  of already distributed images and wider product licences still require review.
- [ ] The pinned Linux wheel links `libgcc_s.so.1`; review GCC Runtime Library
  Exception conditions and actual image runtime notices. Do not call the entire
  native/system dependency chain purely permissive. The project's own licence
  remains unchanged; see the ELF/linkage evidence in `docs/pdf-processing.md`.
- [ ] Preserve `docs/licenses/U2NET-Apache-2.0.txt` and the existing model attribution;
  confirm upstream weight/export provenance, copyright notices and any NOTICE
  obligations before redistribution. Fixed hash verification is not licence review.
- [ ] Check ONNX Runtime MIT, NumPy BSD/component notices, Pillow/HEIF/AVIF codecs,
  pypdf, document/Office packages, MCP/HTTP packages and all transitive native
  libraries against the actual distributed versions and bundled notices.
- [ ] Inventory React/router, Vite/build assets, local fonts (if any), icons and
  other browser-delivered dependencies. No external font or raster asset was
  introduced by these legal pages.
- [ ] Check redistribution obligations for the Docker base images, LibreOffice,
  DejaVu fonts and OS packages, not only Python/npm dependencies. Determine
  whether a consolidated third-party notices/source offer is needed. Existing
  model notices are not a complete product-wide notice inventory.
- [ ] Keep product/file ownership terms distinct from third-party licence rights.

## Authoritative research references

Final update references: [Cloudflare customer DPA](https://www.cloudflare.com/cloudflare-customer-dpa/)
describes its processor/subprocessor scope and incorporation into the main
agreement. This does not establish roles for all Cloudflare activities or verify
this customer's transfer/access facts. The GDPR text below was rechecked; no
new legal-compliance conclusion or invented transfer mechanism was added.

These sources inform a cautious draft; they do not establish its enforceability
or that production complies. Some EUR-Lex HTML requests returned a JavaScript
challenge; official indexed extracts and the additional guidance below were
available. Verify consolidated texts, amendments and effective dates with counsel.
FreeConvert's three pages were inspected for structure only; no wording, corporate
details or security assertions were reused.

- [GDPR, Regulation (EU) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng):
  Articles 5, 6, 12–22, 28, 32–34, 37 and 44–49 as applicable.
- [EDPB guidelines on Article 6(1)(b) in online services](https://www.edpb.europa.eu/system/files/documents/files/file1/edpb_guidelines-art_6-1-b-adopted_after_public_consultation_en.pdf).
- [EDPB small-business international-transfer guide](https://www.edpb.europa.eu/sme/be-compliant/international-data-transfers_en).
- [AZOP rights and controller duties](https://azop.hr/prava-ispitanika-obveze-voditelja-obrade/),
  [legal bases](https://azop.hr/pravni-temelji-za-obradu-osobnih-podataka/) and
  [legitimate interests](https://azop.hr/legitimni-interes-kao-pravna-osnova-za-obradu-osobnih-podataka/).
- [Unfair Terms Directive 93/13/EEC](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31993L0013)
  and [Digital Content/Services Directive (EU) 2019/770](https://eur-lex.europa.eu/eli/dir/2019/770/oj/eng).
- [ePrivacy Directive 2002/58/EC](https://eur-lex.europa.eu/eli/dir/2002/58/oj/eng),
  including terminal-storage rules and relevant national implementation.
- [Croatian Civil Obligations Act](https://narodne-novine.nn.hr/clanci/sluzbeni/2005_03_35_707.html),
  especially Article 345; review all applicable amendments.
- [Croatian Consumer Protection Act](https://narodne-novine.nn.hr/clanci/sluzbeni/2022_02_19_203.html)
  and [2026 amendments with differing commencement dates](https://narodne-novine.nn.hr/clanci/sluzbeni/2026_06_59_728.html).
- [Croatian digital-content/services legislation](https://narodne-novine.nn.hr/clanci/sluzbeni/2021_10_110_1925.html)
  and [Electronic Commerce Act](https://narodne-novine.nn.hr/clanci/sluzbeni/2003_10_173_2504.html),
  with current amendments to be checked.
- Historical removed-renderer references (not current dependencies):
  [PyMuPDF publisher licensing](https://pymupdf.io/licensing) and
  [publisher repository](https://github.com/pymupdf/PyMuPDF).
- Current PDF library licences and distribution evidence are recorded in
  `docs/pdf-processing.md` and `docs/licenses/pdf/`.
- Background model/runtime upstream links and attribution are already recorded in
  `docs/background-removal.md`; that document and bundled licence were not changed.

## Technical review and non-deployment smoke checks

From `frontend/`, run `npm run legal:generate`, `npm run legal:check`, `npm test`,
`npm run typecheck` and `npm run build`. Check the built HTML contains all text,
TOC anchors and tables, with no scripts/inline executable content. Review desktop
and narrow-screen rendering and keyboard navigation. The retention table is a
labelled keyboard-focusable horizontal scroll region rather than body overflow.
The existing site is light-only; no new theme mode was invented.

`legalPages.test.tsx` compares complete article text, URLs and IDs between React
and static HTML, checks trusted markup, Nginx routes/headers, content limitations,
navigation and generation freshness. These checks are not a formal WCAG audit or
an actual production HTTP test. `robots.txt` already allows all public routes;
the sitemap now includes `/security`, so no robots change is needed.

When Docker is available, use an isolated local frontend image, **not** a
production Compose restart, to validate Nginx and raw extensionless responses:

```powershell
docker build -f frontend/Dockerfile -t konvertira-legal-review .
docker run --rm konvertira-legal-review nginx -t
docker run --rm -d --name konvertira-legal-review -p 127.0.0.1:18080:80 konvertira-legal-review
curl.exe -fsS -D - http://127.0.0.1:18080/privacy
curl.exe -fsS -D - http://127.0.0.1:18080/terms
curl.exe -fsS -D - http://127.0.0.1:18080/security
curl.exe -fsS -D - http://127.0.0.1:18080/support
docker stop konvertira-legal-review
```

Confirm the responses contain meaningful policy HTML without executing JavaScript
and all seven existing security headers plus `Cache-Control: no-cache`. Do not
mark Nginx/Docker or public HTTP verification passed unless it actually ran.

## Local implementation and validation record

The following is the historical comprehensive-draft implementation record, not
the changed-file list or newly executed checks for the final factual update.

The original substantive drafts contain approximately 3,420 words in Terms
(28 sections), 3,643 in Privacy (26 sections) and 1,997 in Security (16 sections),
excluding the summary, table of contents and review notices. All three use a
single checked-in content source, with matching React rendering and mechanically
generated standalone HTML. No new dependency, processing behaviour or public
API/MCP schema was introduced.

Files changed/added for this task:

- `docs/legal-review-checklist.md`
- `frontend/README.md`
- `frontend/nginx.conf`
- `frontend/package.json`
- `frontend/scripts/generate-legal-pages.mjs`
- `frontend/public/legal.css`
- `frontend/public/privacy.html`
- `frontend/public/terms.html`
- `frontend/public/security.html`
- `frontend/public/support.html`
- `frontend/public/sitemap.xml`
- `frontend/src/App.tsx`
- `frontend/src/components/Footer.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/css/pages.css`
- `frontend/src/legal/LegalDocument.tsx`
- `frontend/src/legal/privacy.json`
- `frontend/src/legal/terms.json`
- `frontend/src/legal/security.json`
- `frontend/src/pages/PrivacyPage.tsx`
- `frontend/src/pages/TermsPage.tsx`
- `frontend/src/pages/SecurityPage.tsx`
- `frontend/src/pages/SupportPage.tsx`
- `frontend/src/pages/legalPages.test.tsx`

Executed locally:

- `npm run legal:generate` and `npm run legal:check`: passed; checked-in copies
  match their source. The check is read-only and normalises Git CRLF line endings.
- `npm test`: **44 passed, 8 test files passed**, including 22 legal-page checks.
- `npm run typecheck`: passed.
- `npm run build`: passed; Vite production assets and standalone HTML generated.
- Built/static SHA-256 equality: passed for privacy, terms, security and legal CSS.
- Headless Microsoft Edge 155 with bundled Playwright (no project dependency
  added): **15 smoke cases passed** on a temporary local HTTP asset server.
  Twelve cases covered privacy, terms, security and support with JavaScript
  disabled at 320, 390 and 1280 px. Three covered React SPA footer navigation,
  page metadata and section counts at 390 px. No body horizontal overflow was
  found; anchors, keyboard skip links and the focusable retention-table scroll
  region were checked. Mobile screenshots were inspected. This is not a full
  assistive-technology/WCAG audit and does not validate actual Nginx responses.
- Python `compileall` for compatibility entry points, config, backend and MCP:
  passed. No Python source changed; the Python test suite was not rerun here.
- `docker compose config --quiet`: passed.
- `git diff --check`: passed (only Git LF/CRLF conversion warnings).
- Docker daemon was **unavailable** (`dockerDesktopLinuxEngine` named pipe not
  found); no image build, container/Nginx validation or public HTTP test ran.
  No standalone Nginx executable was available either.

No commit, push, merge, deployment, plugin submission or production configuration
change was performed. Existing unrelated roadmap files were left untouched.

## Final factual update — local validation, October 11, 2026

Only these eight files changed in this update:

- `frontend/src/legal/privacy.json`
- `frontend/src/legal/terms.json`
- `frontend/src/legal/security.json`
- `frontend/public/privacy.html` (existing generator)
- `frontend/public/terms.html` (existing generator)
- `frontend/public/security.html` (existing generator)
- `frontend/src/pages/legalPages.test.tsx`
- `docs/legal-review-checklist.md`

Existing structure, section IDs, TOC, React/static parity, navigation, styling,
accessibility markup, direct Nginx routes and support page are preserved. Tests
now cover confirmed operator/infrastructure disclosures and unresolved gates.
Public wording does not promise universal 14-day log deletion, EEA-only access,
exact-second file erasure, permanent free service or exclusively permissive
Docker licensing. Existing consumer, rights, incident and liability safeguards
were retained; their final legal assessment remains open above.

Executed for this update:

- `npm run legal:generate`: passed.
- `npm run legal:check`: passed.
- `npm test`: **46 passed, 8 test files passed**.
- `npm run typecheck`: passed.
- `npm run build`: passed (TypeScript and Vite production build).
- `git diff --check`: passed, only Git LF/CRLF conversion warnings.

No Python, configuration, API/MCP, environment, dependency, licence or model
files changed. No production/Cloudflare settings changed. No fresh remote health,
Docker, browser or deployment checks were performed for this wording update;
operator-confirmed deployed checks are explicitly recorded separately above.
No commit, push, deployment, publication or plugin submission was performed.

## Final legal pages update — local verification, October 11, 2026

Changed only the three legal JSON sources and generated HTML counterparts,
LegalDocument.tsx and the static generator (Last updated / Important information),
legalPages.test.tsx, this checklist, DATA_RETENTION.md and
PRIVACY_SECURITY_CHECKLIST.md. Other internal procedures and application
API/MCP/configuration/security settings were unchanged.

Email and cookie disclosures separate operator-confirmed observations from
unverified provider contracts, retention and other scenarios. Public operator
information stays limited to supplied details; no private identifiers, actual
messages, mailbox address/account IDs or credentials were added. Official email
references: [Cloudflare routing](https://www.cloudflare.com/learning/email-security/what-is-email-routing/)
and [Google privacy](https://policies.google.com/privacy); these do not establish
account-specific contracts or a signed Google DPA.

Local validation: legal:generate and legal:check passed; npm test **50 passed,
8 test files passed** (28 legal-page tests, including static/React text/link/ID
parity); typecheck and production build passed. An initial secret-pattern test
false-positive on the existing words “private keys” was narrowed to actual key
headers and rerun successfully. git diff --check passed (only LF/CRLF warnings).

Technically ready for frontend deployment, not a certification of legal readiness.
Identification/contact-address, registration/consumer duties, provider retention,
roles/transfers, scenario-specific cookies, operational procedures and licensing
review remain open. No commit, push, deployment or plugin submission in this task.
