import { PageIntro } from '../components/PageIntro'

export function PrivacyPage() {
  return (
    <>
      <PageIntro eyebrow="Privacy policy" title="Your files deserve careful handling.">
        This policy explains how Konvertira handles files and related information when you use our service.
      </PageIntro>
      <article className="legal-content">
        <p className="legal-note"><strong>Draft notice:</strong> This policy is a practical starting point and should be reviewed by qualified legal counsel before public launch. Replace bracketed placeholders with final details.</p>

        <h2>1. Information we process</h2>
        <p>When you submit a file, we process the file itself, its filename, selected operation, technical request details, and basic server logs needed to operate and protect the service. We do not require an account for the current version.</p>

        <h2>2. How files are handled</h2>
        <p>Files may be uploaded to and temporarily processed on Konvertira’s servers or infrastructure operated on our behalf. We use each submitted file to perform the operation you requested, such as removing image metadata or converting an image format.</p>
        <p>Uploaded and processed files are scheduled for automatic deletion after <strong>[INSERT RETENTION PERIOD]</strong>. Temporary copies, caches, or backups may follow a separate deletion schedule of <strong>[INSERT APPLICABLE PERIOD]</strong>. These placeholders must be updated to match the production system before launch.</p>

        <h2>3. Metadata</h2>
        <p>Image metadata can include GPS location, camera and device information, capture dates, editing software, and other embedded fields. The amount and type of metadata removed may depend on the file format and processing method. You should verify the output if you have a specific privacy requirement.</p>

        <h2>4. Why we process information</h2>
        <p>We process files and limited technical data to provide the requested service, maintain reliability, prevent abuse, diagnose errors, and meet applicable legal obligations. We do not use uploaded file contents for advertising.</p>

        <h2>5. Service providers and disclosures</h2>
        <p>We may use hosting, storage, security, and infrastructure providers to operate Konvertira. Those providers may process data on our behalf under their applicable terms. We may also disclose information when required by law or when reasonably necessary to protect the service, users, or others.</p>

        <h2>6. Security</h2>
        <p>We use reasonable technical and organizational measures appropriate to the service. No internet service can guarantee absolute security, so avoid uploading files that you do not want processed through a server-based service.</p>

        <h2>7. Your choices and rights</h2>
        <p>Depending on where you live, you may have rights concerning personal data, including access, correction, deletion, or objection. Contact us at <a href="mailto:privacy@konvertira.com">privacy@konvertira.com</a>. We may need information to verify and respond to a request.</p>

        <h2>8. Changes and contact</h2>
        <p>We may update this policy as the service changes. The effective date will be shown here: <strong>[INSERT EFFECTIVE DATE]</strong>. Questions can be sent to <a href="mailto:privacy@konvertira.com">privacy@konvertira.com</a> or <strong>[INSERT LEGAL ENTITY AND ADDRESS]</strong>.</p>
      </article>
    </>
  )
}
