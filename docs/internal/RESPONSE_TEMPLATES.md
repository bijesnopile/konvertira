# Contextual response templates

Internal draft, October 11, 2026; not legally reviewed or operationally tested.
English templates for an authorised owner using [GDPR_REQUESTS.md](GDPR_REQUESTS.md)
and [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md). Replace every bracketed field,
remove inapplicable text and verify facts, recipient identity/channel and deadlines.
Never send a template as an automatic declaration of deletion or compliance.
Actual messages/registers belong in a private store, not this repository.

## GDPR request acknowledgement

Subject: Konvertira privacy request — [reference]

Hello [name or neutral greeting],

We received your request on [received date] concerning [minimal scope/right].
We are assessing the information held by Konvertira and the applicable action.
We will respond without undue delay and generally within one month of receipt;
our recorded response deadline is [date]. If a lawful extension is necessary,
we will explain it within that original period.

Please do not send passwords, identity documents, complete files or private
download links by default. We will ask only for clarification necessary to handle
your request. For privacy correspondence, contact legal@konvertira.com.

Matej Tokić — Konvertira

## Proportionate identity or scope clarification

Subject: Clarification needed — [reference]

Hello [greeting],

To protect personal data and process your request, we need [specific minimum
clarification] because [actual reasonable doubt or scope ambiguity]. Please use
[agreed safe method] to provide [limited information]. Do not send a complete
uploaded file, passwords or an identity-document copy unless a necessary secure
method has separately been agreed. [Representative authority question if relevant.]

Our current response deadline is [date]. We will assess any legal effect of this
clarification on the deadline; this message does not automatically restart it.
If you cannot provide the requested information, let us know so we can consider
a proportionate alternative.

Matej Tokić — Konvertira

## Request completed or partly completed

Subject: Outcome of your privacy request — [reference]

Hello [greeting],

We assessed your [rights] request received on [date]. We checked [specific
controlled locations/time window] and took these actions: [verified action and
date, separately for each right]. [Secure method for qualifying access/portability
data and required contextual information, if applicable.]

[Categories still held and specific lawful reason/review rule, if applicable.]
[Recipient/processor action requested, confirmation received or still pending.]
This outcome concerns the locations and actions stated above; it does not confirm
deletion of copies held by your device, recipients or independent platforms.
[Any limitation and complaint/remedy information from the refusal template.]

If you have relevant additional information or a concern, contact
legal@konvertira.com. You may complain to AZOP or another competent supervisory
authority and seek a judicial remedy where applicable; contacting us first is
not a prerequisite.

Matej Tokić — Konvertira

## No matching data retained or identifiable

Subject: Search outcome — [reference]

Hello [greeting],

We checked [controlled locations, scope and date] using [minimal matching criteria].
We did not find retained personal data matching your request in those locations.
[Explain actual matching limitations or Article 11 inability to identify, if
applicable; distinguish unavailable data from a search not performed.]

Konvertira uses temporary result storage and has no public account-to-file index.
We have not recreated removed files or collected new identifiers solely to
reconstruct processing history. This does not establish deletion from OpenAI,
other independent providers or copies held elsewhere. [Relevant provider boundary
and official rights route, where needed.] If you can supply limited information
that would help identify a relevant record, contact legal@konvertira.com without
resending sensitive originals. You may complain to AZOP or another competent
authority and seek a judicial remedy where applicable.

Matej Tokić — Konvertira

## Lawful extension notice

Subject: Response deadline update — [reference]

Hello [greeting],

We received your request on [date]. Under Article 12(3) GDPR, additional time is
necessary because [specific complexity/number-of-requests explanation, not merely
operator workload]. We are informing you within the original one-month period.
The revised deadline is [date, no more than two additional months]. We will
respond sooner where possible. [Work already completed and remaining scope.]

This extension does not change your rights. For questions contact
legal@konvertira.com; you may complain to AZOP or another competent supervisory
authority and seek a judicial remedy where applicable.

Matej Tokić — Konvertira

## Lawful refusal or partial refusal

Subject: Decision on your privacy request — [reference]

Hello [greeting],

We assessed your request received on [date]. [Completed actions, if any.]
We cannot fulfil [specific part] because [specific facts and applicable legal
exception, proportionate limitation or justified inability to identify].
[Relevant retained categories and lawful reason; redacted alternative or further
minimal clarification where possible.] We have not applied a blanket refusal
merely because the request concerns another person's data or temporary files.

You may complain to the Croatian Personal Data Protection Agency (AZOP):
https://azop.hr/zahtjev-za-utvrdivanje-povrede-prava/ . You may also contact another
competent authority and seek a judicial remedy where applicable. You need not
contact Konvertira first to exercise those rights. If you wish to provide further
relevant information, use legal@konvertira.com.

Matej Tokić — Konvertira

## Security vulnerability report acknowledgement

Subject: Konvertira security report — [reference]

Hello [greeting],

Thank you for privately reporting [minimal safe description]. We received your
report on [date] and are assessing it. [Necessary clarification using harmless
test data, if any.] Please do not send other users' files, credentials or live
download links, and stop testing that may expose data or disrupt service.

We will use this channel for relevant follow-up. This acknowledgement is not
confirmation of exploitation or a reportable breach, a fixed response-time
promise, or permission for unrestricted testing. Konvertira has no established
bug bounty or formal safe-harbour programme.

Matej Tokić — Konvertira; legal@konvertira.com

## Communication to affected individuals — Article 34

**Incident-specific assessment/review required.** Use only after determining the
applicable role, likely high risk and communication obligations. Do not delay a
required communication while waiting for perfect facts/review. Tailor language
to affected people. Do not include exploit details, tokens or other people's data.

Subject: Important information about your data and Konvertira — [safe reference]

Hello [greeting],

We are contacting you because [plain-language description of the personal-data
breach and how the person is affected]. [Known incident period; uncertainties
clearly separated.] The affected information includes [verified categories, not
unnecessary copies]. The likely consequences are [specific risks and uncertainty].

We have taken [verified containment/mitigation] and are taking [planned measures].
You can reduce the risk by [incident-specific practical steps]. [Explain any
remaining risk; do not state all copies were erased or the issue is fully resolved
unless supported.] We will provide relevant updates through [safe channel].

For questions contact Matej Tokić at legal@konvertira.com [other verified necessary
contact details in actual notice, not a fictional DPO]. You may contact AZOP or
another competent supervisory authority. This message does not require you to
send identification documents, passwords or files.

Matej Tokić — Konvertira

## Regulatory breach notice preparation — not a ready-to-send notice

Use AZOP's current official form/channel from
[reporting guidance](https://azop.hr/izvjescivanje-o-povredi-osobnih-podataka/),
not an ordinary acknowledgement template. Incident-specific review must cover:
assessed controller/processor role and competent authority; actual operator/contact
details; awareness and notification times; breach nature; categories/approximate
people and records; likely consequences; measures taken/proposed; unknowns;
reasons for any delay; individual communication decision; phased update plan.
Follow [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) for deadlines and assessment.
Neither this checklist nor provider notification alone fulfils Article 33.
