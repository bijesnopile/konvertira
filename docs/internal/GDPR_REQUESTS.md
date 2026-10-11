# GDPR request handling

Status: internal procedure draft, October 11, 2026. Not tested, formally adopted
or legally reviewed. Proposed responsible owner: Matej Tokić; owner acceptance,
mailbox monitoring and absence cover must be recorded before operational use.
No DPO, response team or guaranteed GDPR compliance is implied.

Use with [retention inventory](DATA_RETENTION.md), [response templates](RESPONSE_TEMPLATES.md),
[routine checklist](PRIVACY_SECURITY_CHECKLIST.md) and [incident response](INCIDENT_RESPONSE.md).
These repository files contain blank templates only. Keep actual cases in an
owner-selected access-controlled store **outside Git, public issues and web roots**.
Use encryption appropriate to the store, restricted access and secure delivery;
these are actions to implement, not existing verified controls.

## 1. Receive, record and calendar

1. Receive privacy requests at `legal@konvertira.com`. A request arriving through
   support or another valid channel still counts: route it privately without
   resetting receipt time or requiring a special form/GDPR wording.
2. Open an internal reference such as `[request-reference]`; record received date,
   time/timezone, requested rights and enough contact information to answer. Do
   not attach the complete source file or token to the register. Acknowledge using
   the template after adapting it; acknowledgement is not the substantive reply.
3. Calendar action **without undue delay and generally within one month of
   receipt**, not 30 days. Calculate the corresponding date in the following
   month, including month-end and applicable non-working-day rules; verify any
   uncertain calculation and set an earlier internal reminder. Record the basis.
4. An extension of up to two further months is possible where justified by
   complexity or number of requests. Inform the requester within the original
   month, give specific reasons and the revised deadline. Solo workload alone is
   not an automatic extension. Do not silently restart/pause the clock while
   asking for clarification or ID; assess applicable rules with advice if needed.

## 2. Clarify scope and identity proportionately

Ask for the operation, approximate time and relevant correspondence if needed.
Do not demand a file re-upload, passwords, signed URLs, full conversation history
or identity documents by default. A verified existing correspondence channel or
narrow factual clarification may suffice. An IP address or possession of a result
URL alone does not establish that a person owns all data in the file.

If reasonable identity doubts exist, record why and ask only what resolves them.
Verify authority for a representative and protect children/third parties without
inventing a universal age threshold. If exceptional document verification is
necessary, agree a secure method, allow unrelated fields to be obscured, record
the result rather than a retained copy and remove verification material when no
longer necessary. Do not disclose data while verification remains insufficient;
do not obstruct a request with excessive verification.

## 3. Search only relevant, controlled locations

Record a bounded search scope and results for each location in the inventory:

- Legal/support correspondence and any existing private request/incident records.
- Backend and MCP result stores, **separately**. They contain random token-based
  names, not user accounts or a searchable user-to-file mapping. Use a securely
  supplied locator only when necessary, verified and authorised. Store any
  indispensable locator separately with restricted access, not in the register.
- Relevant temporary conversion workspaces and upload spooling only where an
  identified job or orphan exists; do not open unrelated users' files to hunt for
  names. Inputs may be in memory; do not dump process memory or reconstruct
  deleted files just to manufacture a response.
- Narrow time/service windows in Docker, journal and operator-accessible request
  information. IPs can be shared or change; filenames, paths and tokens may be
  sensitive. Do not treat a coincident IP/time as reliable identity. Redact other
  people, secrets and irrelevant events before disclosure.

The default stored-result TTL is 900 seconds from the stored creation timestamp
in private expiry metadata, not an index of persons. Resolution/delivery now deny
expired access independently of unlink; legacy records without metadata are
unavailable. Startup, periodic and resolution cleanup can fail physically; inspect
only relevant actual locations rather than inferring deletion from elapsed time.
If no matching data remains, state which locations and scope were checked and
what could not be matched. Absence in a store is not proof of erasure from all
providers or recipient devices. Article 11 does not require retaining additional
identifiers solely to identify people; consider information a requester can
lawfully supply and explain inability to identify where applicable.

## 4. Decide and perform the applicable action

| Right | Practical decision/action |
| --- | --- |
| Access | Establish whether relevant personal data is held; provide a secure intelligible copy and required Article 15 information (purposes, categories, recipients, retention, source, rights and applicable safeguards), not only a download link or a copy of the policy. Protect others by proportionate redaction, not automatic blanket refusal. |
| Rectification | Correct inaccurate controlled correspondence/records or add an appropriate statement. Distinguish data correction from offering a new file conversion; do not claim to alter originals or copies already held elsewhere. |
| Erasure | Assess Article 17 conditions/exceptions. Remove identified controlled data when required, confirm exact targets and active-job state first; do not issue wildcard/recursive deletes. Record what was removed, unavailable or lawfully retained and why. There is no public rights/deletion API in this implementation. |
| Restriction | Assess Article 18. Preserve only the relevant data under restricted access with a documented reason; pause applicable processing where required. There is no built-in per-user legal hold. Arrange a minimal protected hold only if necessary, prevent automatic cleanup of that specific held copy and assess provider instructions; notify before lifting restriction where required. |
| Objection | Assess Article 21 grounds for the actual purpose and stop processing unless a lawful exception applies. Document any compelling overriding grounds/claims; legitimate-interest processing is not automatically exempt. Current product has no direct marketing. |
| Portability | Assess Article 20: consent/contract basis and automated processing, plus scope of data provided by the person. Supply qualifying data in a structured commonly used machine-readable format and assess direct transfer if technically feasible. Do not promise a copy of every derived output or third-party record. |
| Consent withdrawal | Identify a purpose actually relying on consent; stop that future consent-based processing and assess erasure separately. Current requests/Terms are not blanket consent; withdrawal does not undo prior lawful processing or all other lawful bases. |

Where Article 19 applies, communicate rectification, erasure or restriction to
relevant recipients unless impossible or disproportionate; document the grounds
and inform the person about recipients if requested. Handle public disclosures
under Article 17(2) where applicable. Do not send another person's file to verify
a request or reveal their identity in a response.

## 5. Provider and platform boundaries

The operator remains responsible for searches/actions under his control. When a
provider processes on his behalf, use the applicable contractual/DPA assistance
channel, minimum necessary facts and record instructions, acknowledgement and
outstanding actions. No provider is contacted by creation of this document.

Cloudflare/Contabo can have different roles for different activities. Their
independent-controller records are not automatically searchable/deletable by
Konvertira; explain boundaries and point to official provider rights channels
when relevant without dismissing Konvertira's own obligations. OpenAI handles
ChatGPT accounts/conversations independently; Konvertira has selected references
and tool parameters, not unrestricted conversation access. Konvertira expiry does
not delete OpenAI records. Do not automatically designate OpenAI a processor.

## 6. Reply, limitations and closure

Give the outcome by right, actual actions/locations, any uncertainty and any
lawfully retained categories. Refusal/partial refusal needs a specific valid
exception and recorded reasoning. For manifestly unfounded/excessive requests,
the operator bears the burden of justification; assess Article 12(5), rather
than charging automatically. For inaction, explain reasons and complaint/judicial
remedy rights within the applicable month. Use professional advice for doubtful
cases; advice must not become a reason to miss notification/response duties.

Provide [AZOP complaint information](https://azop.hr/zahtjev-za-utvrdivanje-povrede-prava/)
and competent-authority/court rights without requiring prior contact with the
operator. Send the response through a verified secure channel, separately from
other people's data; the temporary bearer download route is not an authenticated
rights-response portal. Record delivery and outstanding provider follow-up.

At closure, minimise the record, remove unnecessary verification material and
set a justified retention/review date using [DATA_RETENTION.md](DATA_RETENTION.md).
No request-record retention period is currently confirmed. Document purpose,
legal basis, applicable obligation/claim period, access and eventual deletion;
do not retain complete files indefinitely as proof of handling.

## Minimal private request register — blank template

| Field | Entry |
| --- | --- |
| Internal reference | [request-reference] |
| Received date/time/timezone; channel | [received] |
| Request category and minimal scope | [rights / operation / approximate time] |
| Relevant service/processing; role | [local / backend / MCP / correspondence; assessed role] |
| Verified response contact | [restricted contact reference, not unnecessary identifiers] |
| Identity/representative verification needed; reason; completed | [minimal decision/result/date] |
| Original deadline; calculation; reminder | [dates and basis] |
| Extension reason/date notified; revised deadline | [if applicable] |
| Locations checked; search date/scope; matching limitations | [bounded findings] |
| Action taken; deletion technically possible? | [exact outcome, not file contents] |
| Recipient/processor instructions and follow-up | [minimal references] |
| Answered date/channel; outcome | [completed / partial / no match / refused] |
| Refusal/retention exception and rationale | [specific basis, if applicable] |
| Closure; retention justification; review/deletion date | [owner decision] |

No passwords, access tokens, signed links, full uploads or unnecessary personal
data belong in this register. Private records must never be committed here.

## Basis and review

Consult [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng), Articles 5, 11–22
and 28, and [EDPB access guidance](https://www.edpb.europa.eu/documents/guideline/guidelines-012022-on-data-subject-rights-right-of-access_en).
This is a practical draft, not an enforceability/compliance opinion. Unresolved
roles, identity disclosures and contracts remain in the [legal checklist](../legal-review-checklist.md).
