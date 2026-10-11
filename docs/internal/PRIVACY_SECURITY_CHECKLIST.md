# Proportionate privacy and security operating routine

Internal draft, October 11, 2026. Documented does not mean adopted, assigned,
tested or legally reviewed. Proposed owner: Matej Tokić, independent natural
person based in Croatia; formal acceptance and absence arrangements are pending.
This is a suggested solo-operator routine, not a claim of continuous monitoring.

Related: [requests](GDPR_REQUESTS.md), [incidents](INCIDENT_RESPONSE.md),
[retention](DATA_RETENTION.md), [templates](RESPONSE_TEMPLATES.md),
[publication gates](../legal-review-checklist.md).

## Before adoption

- [ ] Owner accepts responsibility and records who can act during absence, without
  inventing a team. Establish realistic mailbox-check habits and deadline reminders;
  weekly maintenance is not an acceptable delay for a time-sensitive incident.
- [ ] Select a private access-controlled record/evidence store outside Git/web
  roots; establish secure access/delivery, retention review and recovery. Store
  credentials only in an appropriate separate credential manager, not these docs.
- [ ] Verify legal/support mailbox access/delivery, provider assistance and current
  authority submission channels. Record necessary contacts privately.
- [ ] Confirm actual production mounts, effective TTL, cleanup and logging settings;
  source defaults and past provider panel confirmations are not live assurance.
- [ ] Run a synthetic request exercise: receipt, calendar-month deadline including
  month-end, minimal identity checks, no-match reply, partial response, extension,
  secure delivery, record review/deletion. Do not use real customer content.
- [ ] Run a synthetic incident tabletop: harmless exposed result link, volume/log
  exposure and provider notice; record awareness time, risk and notification
  decisions. No attacks, live-token publication or destructive production tests.
- [ ] Obtain proportionate legal review of roles, deadlines, exceptions, records
  and publication gates; no compliance claim follows from completing this list.

## Weekly maintenance

- [ ] Review narrow windows of unexpected errors, repeated rejection/crash patterns
  and administrator/provider alerts. Minimise access to user content and redact
  paths/tokens before sharing. Ordinary errors are not automatically breaches.
- [ ] Check frontend/backend/MCP health and unusual storage growth. Health is a
  responsiveness signal, not proof of every engine, model or cleanup worker.
- [ ] Check both result stores using counts, sizes and age metadata first. Use
  harmless test outputs to verify expiry/download unavailability after the actual
  TTL and cleanup interval. Investigate overdue files/errors; do not mass-download
  user files or run wildcard deletion. Distinguish active jobs from orphan
  LibreOffice/upload temporary files before safe targeted recovery.
- [ ] Review open request deadlines, provider follow-ups and incident actions.
  Take urgent action when discovered, not only at the next weekly slot.

## Monthly review

- [ ] Review dependency/security advisories for actual pinned Python/npm/native
  and Docker/Office/model components; document relevance and safe update/test
  plan. This does not authorise automatic updates or current production changes.
- [ ] Review Docker disk/volume/log growth and journal disk usage. Inspect only
  logging-driver/options needed to confirm json-file 10m/3 on frontend, backend,
  MCP and separate-stack Caddy; avoid full inspect/env dumps. Verify effective
  journal 100M/14day controls; they do not set Docker/Cloudflare retention.
- [ ] Review admin/provider/email access, unnecessary accounts and available MFA
  or session controls. Availability/configuration must be verified, not assumed.
  Never paste credentials, account IDs, private addresses or provider attachments
  into this repository. Plan needed changes privately with owner authorisation.
- [ ] Test support/legal mail delivery and monitored access using harmless messages.
- [ ] Verify Cloudflare RUM automatic injection remains disabled, Logpush remains
  inactive, and proxy/security/cookie/log settings have not unexpectedly changed.
  Do not equate disabled RUM with absence of technical request logging.
- [ ] Verify Contabo customer backup/snapshot state and review any newly documented
  provider retention/access/transfer facts; no automatic snapshot creation.
- [ ] Review closed case retention dates, narrow evidence holds and deletion
  outcomes. Retain a minimal action record, not unnecessary user files/IDs.

## After a material change or significant incident

- [ ] Map changed data flows: local/server boundary, input spooling/workspaces,
  result stores, browser storage and access/diagnostic information.
- [ ] Review Privacy, Terms and Security wording against actual operation; propose
  separate approved updates rather than silently publishing a new claim.
- [ ] Assess new recipients, roles, subprocessors, transfers, contracts and
  legal bases; check relevant GDPR records/risk/DPIA duties where applicable.
- [ ] Review TTL, cleanup error paths, active-thread behaviour, logging, retention,
  backup/restore scope and removal of expired temporary data.
- [ ] Reassess request/incident templates, practical response/delivery capability,
  owner/absence arrangements and notification channels. Repeat relevant synthetic
  exercises and record what was tested, limits and corrective actions.
- [ ] Review third-party distribution notices/provenance, including PDFium native
  and linked OS/GCC exception obligations; permissive wrappers are not a blanket
  licence conclusion for the Docker image.

## Minimal private check record and adoption status

Record date, owner, check scope, source vs actual evidence, redacted result,
action/next due date and remaining uncertainty. Keep operational/private values
outside Git. Missed checks should be recorded and rescheduled, not falsely marked
complete. This routine does not guarantee detection or a 24/7 incident response.

| Milestone | Current status | Evidence needed |
| --- | --- | --- |
| Procedure documented | Drafted October 11, 2026 | Five internal template documents |
| Responsibility assigned/accepted | Pending | Owner acceptance, mailbox habits and absence plan |
| Procedure tested | Pending | Synthetic request and incident exercise results |
| Legal review completed | Pending | Reviewed roles, notices, exceptions and justified record schedule |

Documentation-only validation of Markdown/source consistency is not one of these
operational exercises. Final publication blockers remain in the legal checklist.
