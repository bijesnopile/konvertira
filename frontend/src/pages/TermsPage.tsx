import { PageIntro } from '../components/PageIntro'

export function TermsPage() {
  return (
    <>
      <PageIntro eyebrow="Terms of service" title="Clear terms for a simple service.">
        These terms describe the basic rules for using Konvertira.
      </PageIntro>
      <article className="legal-content">
        <h2>1. Acceptance</h2>
        <p>By using Konvertira, you agree to these terms and the Privacy page. If you do not agree, do not use the service. You must be legally able to enter into this agreement in your jurisdiction.</p>
        <h2>2. The service</h2>
        <p>Konvertira provides file conversion and metadata-cleaning tools. Depending on the selected tool, files may be processed locally in your browser or uploaded for server-side processing. The interface identifies the applicable processing mode.</p>
        <p>Features, supported formats, file limits, and availability may change as this independently operated project develops.</p>
        <h2>3. Your files and responsibilities</h2>
        <p>You retain any rights you hold in your files. Supported browser-side image operations are processed locally on your device and are not uploaded to Konvertira's server. When you explicitly use a server-backed tool, including Konvertira through ChatGPT, the file may be transferred to or retrieved by Konvertira's server for temporary processing. You give Konvertira permission to process it only as needed to provide and operate the requested service.</p>
        <p>You are responsible for having the right to process each file and for keeping appropriate backups. You must not use Konvertira for unlawful content, rights violations, malware distribution, interference with the service, or attempts to bypass service limits and security controls.</p>
        <h2>4. Output and availability</h2>
        <p>Browser and server conversions may change compression, metadata, color profiles, formatting, or other file properties. Results may not be complete or suitable for every purpose. Check downloaded files before relying on them or deleting the originals.</p>
        <p>The service is provided on an “as available” basis, subject to warranties that cannot legally be excluded.</p>
        <h2>5. Liability</h2>
        <p>To the fullest extent permitted by applicable law, Konvertira is provided without guarantees of uninterrupted or error-free operation. Konvertira is not liable for indirect, incidental, special, consequential, or similar losses arising from the use of the service, including loss of data, loss of files, or loss resulting from conversion errors.</p>
        <p>You are responsible for keeping backups of important files and verifying processed output before relying on it.</p>
        <p>Nothing in these terms excludes or limits liability where such exclusion or limitation is prohibited by applicable law, including any mandatory consumer rights.</p>
        <h2>6. Governing terms</h2>
        <p>These terms are governed by the laws of the Republic of Croatia.</p>
        <p>If you are a consumer, any mandatory consumer protections and jurisdiction rights available to you under the laws of your country of residence remain unaffected.</p>
        <p>Where legally permitted, disputes relating to these terms or the service will be subject to the jurisdiction of the competent courts in Croatia.</p>
        <h2>7. Changes and contact</h2>
        <p>These terms may be updated as the service changes.</p>
        <p>Effective date: October 5, 2026.</p>
        <p>For questions about these terms, contact: <a href="mailto:legal@konvertira.com">legal@konvertira.com</a>.</p>
        <p>Konvertira is an independently operated project based in Croatia.</p>
      </article>
    </>
  )
}
