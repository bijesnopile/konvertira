import { PageIntro } from '../components/PageIntro'

export function TermsPage() {
  return (
    <>
      <PageIntro eyebrow="Terms of service" title="Clear terms for a simple service.">
        These terms describe the basic rules for using Konvertira.
      </PageIntro>
      <article className="legal-content">
        <p className="legal-note"><strong>Draft notice:</strong> These terms require legal review before public launch. Replace bracketed placeholders with approved language.</p>

        <h2>1. Acceptance</h2>
        <p>By using Konvertira, you agree to these terms and our Privacy Policy. If you do not agree, do not use the service. You must be legally able to enter into this agreement in your jurisdiction.</p>

        <h2>2. The service</h2>
        <p>Konvertira provides file conversion and metadata cleaning tools. Features, supported formats, file limits, and availability may change. We may suspend or discontinue parts of the service when reasonably necessary.</p>

        <h2>3. Your files and responsibilities</h2>
        <p>You retain any rights you hold in files you submit. You give us permission to process those files only as needed to provide and operate the requested service. You are responsible for having the right to upload each file and for keeping appropriate backups.</p>
        <p>You must not use Konvertira to process unlawful content, violate intellectual property or privacy rights, distribute malware, interfere with the service, or attempt to bypass service limits or security controls.</p>

        <h2>4. Output and availability</h2>
        <p>Conversions and metadata removal may not be complete or suitable for every purpose. You are responsible for checking downloaded files before relying on, publishing, or deleting your originals. The service is provided on an “as available” basis, subject to any warranties that cannot legally be excluded.</p>

        <h2>5. Liability</h2>
        <p>To the extent permitted by applicable law, liability limitations and exclusions will be specified after legal review: <strong>[INSERT APPROVED LIMITATION OF LIABILITY]</strong>. Nothing in these terms excludes rights or liability that cannot legally be excluded.</p>

        <h2>6. Governing terms</h2>
        <p>The governing law, jurisdiction, and dispute process will be: <strong>[INSERT GOVERNING LAW AND DISPUTE TERMS]</strong>.</p>

        <h2>7. Changes and contact</h2>
        <p>We may update these terms and will publish the revised version with an effective date. Effective date: <strong>[INSERT DATE]</strong>. Contact: <a href="mailto:legal@konvertira.com">legal@konvertira.com</a> or <strong>[INSERT LEGAL ENTITY AND ADDRESS]</strong>.</p>
      </article>
    </>
  )
}
