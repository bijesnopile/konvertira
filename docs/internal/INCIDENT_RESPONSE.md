# Security incident and personal-data breach response

Internal draft — October 11, 2026. Not exercised, adopted or legally reviewed.
Proposed decision owner: Matej Tokić; acceptance, secure provider access and absence
arrangements remain to be established. No SOC, 24/7 staffing, certification,
penetration-testing programme or guaranteed response time is claimed. Instructions
are for an authorised operator during a real incident, **not authorisation to
change production during this documentation task**.

Use [retention inventory](DATA_RETENTION.md), [templates](RESPONSE_TEMPLATES.md),
[GDPR requests](GDPR_REQUESTS.md) and [routine checks](PRIVACY_SECURITY_CHECKLIST.md).
Keep actual incident evidence/registers outside this repository and public issues,
in a restricted, appropriately encrypted store selected and tested by the owner.

## Initial triage checklist

- [ ] Record detection time/source, service and minimal symptom; allocate reference.
- [ ] Separate suspicion, confirmed facts and unknowns. Is harm continuing?
- [ ] Record when there is reasonable certainty of a security incident compromising
  personal data: **awareness time**, not merely the first alert. Investigate promptly;
  do not postpone awareness until every detail or legal opinion is available.
- [ ] Identify confidentiality, integrity and availability effects and persons/data.
- [ ] Decide smallest effective containment; protect a safe administrator channel.
- [ ] Preserve only necessary evidence before it rotates, unless doing so would
  delay urgent harm prevention. Record actions/time and any lost evidence.
- [ ] Assess role, authority/individual notification thresholds and deadlines now.
- [ ] Assign next action, next reassessment time and required provider follow-up.

Signals include private reports to `legal@konvertira.com` or support, abnormal
storage growth, unexplained downloads, repeated parser crashes, provider notices,
unexpected configuration changes and administrator-account alerts. An ordinary
conversion error, rejected malformed file, rate-limit response or unsuccessful
attack is **not automatically a personal-data breach**. Conversely, loss or
unavailability of personal data can be a breach without public disclosure.

## 1. Scope, containment and evidence

Identify frontend, backend, MCP, Caddy, VPS administrator access and relevant
Cloudflare/Contabo/email dependencies separately. Determine affected time window,
versions, data categories, approximate people/records and possible recipients.
Do not assume volume exposure is limited to the currently active result files;
consider metadata/logs and past access. There is no comprehensive user-job audit
trail or account mapping in the application.

Choose reversible targeted containment where possible: restrict an affected
route/service, stop new affected jobs, revoke compromised access or isolate a
compromised host through a trusted control channel. Record authority, rationale,
scope and effects. Do not weaken host allowlists, quotas, TLS or security headers
to troubleshoot. A response timeout does not terminate native thread work;
account for continuing jobs before deletion/recovery. Service interruption alone
does not stop a malicious host administrator.

Never publish logs, bearer links, credentials or original files in GitHub issues.
Preserve narrow time windows and minimum artefacts, with acquisition time,
source, collector, restricted location and integrity hash where useful. Hashes
identify an artefact, not prove no breach. Redact secrets/third parties from working
copies; keep indispensable originals under tighter access. Do not make a blanket
snapshot/volume backup containing all users' uploads just for convenience. If an
exceptional forensic copy is necessary, justify scope, access and deletion review.
Do not wipe logs, prune volumes or reinstall before evaluating evidence needs;
urgent containment takes priority over perfect evidence collection.

## 2. Scenario playbook

| Scenario | Contain and determine scope | Evidence/risk/recovery checks |
| --- | --- | --- |
| Temporary download link exposed | Privately identify the exact backend/MCP result. If authorised and appropriate, revoke access by removing the exact result or temporarily restricting its route; no built-in single-token revocation API exists. Do not click or redistribute live links for testing. | Check whether the file still exists and any available access window/logs. Anyone with a valid link can download; expiry cannot recall copies. Do not equate a user intentionally sharing their own link with a service breach, but assess other people/data and operator disclosure separately. |
| Unauthorised Docker volume access | Restrict offending container/host/account access and new affected writes; treat host-level access as wider than one volume. | Record actual mount/permission and access evidence; inspect only necessary file metadata. Assess both result stores and orphan workspaces. Restore correct privileges after root-cause repair; do not chown broadly or expose mounts. |
| Accidentally public Caddy or Docker logs | Close unintended public access and revoke disclosed secrets/links where applicable. | Identify the published time window/copies, IPs, paths, tokens and diagnostic data. Size rotation does not recall exports or establish who read them. Work with recipients/providers for removal where possible. |
| Compromised VPS admin credentials | Use a trusted recovery device/channel; revoke sessions and affected credentials, restrict access, check persistence and lateral movement. | Review provider/host/SSH access and affected secrets privately. If trust cannot be restored, plan clean rebuild from reviewed artefacts after proportionate evidence preservation. No secrets or real admin details in the register. |
| Malicious/malformed upload | Reject/isolate the affected operation; preserve a minimal safe indicator if necessary, do not rerun the file on production or a personal workstation. | Distinguish a caught parser error from execution, exfiltration or availability harm. Review codec/Office/native engine and limits; reproduce with harmless fixtures in an isolated test environment, patch and verify before recovery. |
| Cloudflare/Contabo incident | Verify an authentic provider notice through an existing trusted channel; determine affected products/time/data and contractual role. | Request scope, containment, retained copies, access locations and assistance as necessary under the applicable contract. Provider assessment does not replace the operator's own risk/deadline assessment. Do not wait for a final vendor report to act. |
| Accidental metadata disclosure | Stop the incorrect output/disclosure path and revoke affected stored reports where feasible. | Names/GPS/authors can be personal data even if image contents were cleaned. Establish actual recipients and categories; test a harmless regression fixture. Successful metadata removal never guarantees anonymity/redaction. |
| Unexpected temporary-file retention | Check effective TTL, expiry sidecars, worker state, actual mounts, filesystem errors and active jobs; contain access to inappropriate retained data. | The local download fix denies expired access independently of unlink; confirm deployed version and use harmless expiry tests, not real user downloads. Physical residue can remain. Distinguish overdue results from separate input/workspace cleanup. Delete exact confirmed orphan targets only after hold/evidence review; record failures and verify recovery. Retention failure is not automatically reportable, but assess unlawful retention, access and harm. |

## 3. Personal-data risk and notification decisions

Assess nature/sensitivity (including faces, children, GPS, documents and metadata),
identifiability, volume, duration, recipients, credible misuse, safeguards, and
possible discrimination, financial loss, identity fraud, confidentiality loss or
availability harm. Record uncertainty and mitigating evidence; a small file count
does not mean low risk. HTTPS or unguessable tokens do not make exposed server
files unintelligible to an unauthorised recipient.

1. **Not a personal-data breach:** record the assessed facts and technical fix;
   reassess if new evidence changes the conclusion.
2. **Breach as controller:** Article 33 notification to the competent supervisory
   authority is required unless unlikely to result in risk to persons' rights and
   freedoms. Notify without undue delay and, where feasible, within **72 hours
   of awareness** (elapsed hours, including weekends). Calendar awareness + 72
   hours and earlier reassessment. If late, explain reasons; do not suppress a
   required notice because the deadline passed. Document every personal-data
   breach, effects, remedies and notification/non-notification reasoning.
3. **Konvertira acting as processor:** notify the relevant controller without
   undue delay under Article 33(2) and agreed assistance arrangements; this is
   not permission to wait 72 hours. Coordinate roles without assuming every
   upload or provider uses the same role. Determine own controller obligations
   separately where applicable.
4. **Likely high risk:** assess Article 34 communication to affected individuals
   without undue delay, in clear language. This is not the same threshold/deadline
   as authority notification. Any exception (effective unintelligibility measures,
   subsequent removal of high risk, or disproportionate effort with equally
   effective public communication) needs documented incident-specific grounds.
   Do not invoke encryption solely because traffic used HTTPS.

Use [AZOP's current reporting guidance](https://azop.hr/izvjescivanje-o-povredi-osobnih-podataka/)
to verify the current form, submission method and competent authority; assess
cross-border jurisdiction where relevant. Do not invent a registered-company
identity, DPO or private address. Required real contact details must be securely
supplied by the owner in the actual notice. Where incomplete, notify in phases
without undue further delay: describe breach nature, categories/approximate counts,
contact point, likely consequences and measures taken/proposed. Record updates,
delivery and any reasons for delay. Regulatory notices require incident-specific
assessment/review; do not wait for perfect knowledge or review to miss duties.

No user account/contact database exists for file jobs. Use only legitimately
available contact details; consider authority guidance and lawful effective public
communication if individual notification is impracticable. Do not reidentify
people by mass-opening expired files or exposing them in a public incident notice.

## 4. Coordination, recovery and lessons

Use trusted contractual provider channels and share minimum necessary facts.
Distinguish operator-controlled data, processor assistance and independent
OpenAI/Cloudflare/Contabo activities. Identify assistance obligations, references
and follow-up dates; do not promise provider erasure. Communicate through the
verified safe contact channel; avoid detailed exploit instructions in public copy.

Recover only after cause and residual access are assessed: patch/rebuild where
necessary, verify privileges/mounts/host allowlists, result permissions, logging
and cleanup. Use harmless fixtures for affected web/MCP paths and check health
**and** operation results; health alone is not engine readiness. Record any
controlled restoration (do not restore expired temporary user files casually),
monitor proportionately for recurrence, and decide when restrictions can end.

Close with timeline, root cause, risk/notification decisions, corrective actions,
owner/dates and a short lesson review. Set evidence/register retention and review
according to [DATA_RETENTION.md](DATA_RETENTION.md); Article 33(5) accountability
does not require indefinite retention of complete uploads. Reopen if facts change.

## Minimal private incident register — blank template

| Field | Entry |
| --- | --- |
| Reference; detection date/time/timezone/source | [incident-reference / minimal signal] |
| Owner; next reassessment/action | [accepted owner / time] |
| Awareness time and basis; 72-hour deadline if applicable | [time / rationale / deadline] |
| Services/time window; facts vs unknowns | [bounded scope] |
| Data/people categories; approximate records/people | [estimates and uncertainty] |
| Confidentiality/integrity/availability effects | [assessment] |
| Containment/evidence location, access, hashes | [safe references only] |
| Role; risk/high-risk rationale; Article 33/34 decisions | [specific assessment, including non-notification] |
| Providers/controller/authority/individual notices | [time/channel/reference; delayed/phased reasons] |
| Recovery checks; residual risk; corrective actions | [findings / owner / due dates] |
| Closure; retention justification/review/deletion | [decision] |

No live links/tokens, credentials, complete files or unnecessary personal details.

## Guidance

[GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng), Articles 4(12), 32–34;
[EDPB breach guidance 9/2022](https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-92022-personal-data-breach-notification-under_en);
[AZOP reporting guidance](https://azop.hr/izvjescivanje-o-povredi-osobnih-podataka/).
Legal review and operational testing remain outstanding in the [legal checklist](../legal-review-checklist.md).
