import { PageIntro } from '../components/PageIntro'

export function SupportPage() {
  return (
    <>
      <PageIntro eyebrow="Support" title="How can we help?">
        Get help with Konvertira or report a technical issue.
      </PageIntro>
      <article className="legal-content">
        <h2>Contact support</h2>
        <p>For general help, email <a href="mailto:support@konvertira.com">support@konvertira.com</a>.</p>
        <p>Include the tool you used, the input and output formats, your browser, and a description of what happened. Error messages and screenshots are helpful, but do not send private, sensitive, or confidential files by email.</p>
        <h2>Technical and project issues</h2>
        <p>For reproducible bugs, feature ideas, or project questions, visit the <a href="https://github.com/bijesnopile/konvertira" target="_blank" rel="noopener noreferrer">Konvertira GitHub repository</a>.</p>
        <h2>Legal questions</h2>
        <p>For legal notices or questions about the Terms or Privacy page, email <a href="mailto:legal@konvertira.com">legal@konvertira.com</a>.</p>
        <h2>Security and data handling</h2>
        <p>Read <a href="/security">Security &amp; Data Handling</a> for safeguards and limitations. Report suspected vulnerabilities privately to <a href="mailto:legal@konvertira.com">legal@konvertira.com</a>; do not post sensitive files or live download links in public issues.</p>
      </article>
    </>
  )
}
