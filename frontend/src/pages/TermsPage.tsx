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
        <p>By using Konvertira, you agree to these terms and the Privacy page. If you do not agree, do not use the service. You must be legally able to enter into this agreement in your jurisdiction.</p>

        <h2>2. The service</h2>
        <p>Konvertira provides file conversion and metadata-cleaning tools. Depending on the selected tool, files may be processed locally in your browser or uploaded for server-side processing. The interface should identify the applicable processing mode.</p>
        <p>Features, supported formats, file limits, and availability may change as this independently operated project develops.</p>

        <h2>3. Your files and responsibilities</h2>
        <p>You retain any rights you hold in your files. Local image operations do not require Konvertira to receive the file. When you explicitly use a server-backed tool, you give Konvertira permission to process the uploaded file only as needed to provide and operate the requested service.</p>
        <p>You are responsible for having the right to process each file and for keeping appropriate backups. You must not use Konvertira for unlawful content, rights violations, malware distribution, interference with the service, or attempts to bypass service limits and security controls.</p>

        <h2>4. Output and availability</h2>
        <p>Browser and server conversions may change compression, metadata, color profiles, formatting, or other file properties. Results may not be complete or suitable for every purpose. Check downloaded files before relying on them or deleting the originals.</p>
        <p>The service is provided on an “as available” basis, subject to warranties that cannot legally be excluded.</p>

        <h2>5. Liability</h2>
        <p>To the extent permitted by applicable law, liability limitations and exclusions will be specified after legal review: <strong>[INSERT APPROVED LIMITATION OF LIABILITY]</strong>. Nothing in these terms excludes rights or liability that cannot legally be excluded.</p>

        <h2>6. Governing terms</h2>
        <p>The governing law, jurisdiction, and dispute process will be: <strong>[INSERT GOVERNING LAW AND DISPUTE TERMS]</strong>.</p>

        <h2>7. Changes and contact</h2>
        <p>These terms may be updated as the service changes. Effective date: <strong>[INSERT DATE]</strong>. Contact: <a href="mailto:legal@konvertira.com">legal@konvertira.com</a> or <strong>[INSERT LEGAL ENTITY AND ADDRESS]</strong>.</p>
      </article>
    </>
  )
}
