import privacy from './privacy.json'
import terms from './terms.json'
import security from './security.json'

export const legalDocuments = { privacy, terms, security }
export type LegalSlug = keyof typeof legalDocuments

// Body fragments are reviewed, checked-in policy copy only. Never pass user,
// upload, API or MCP data into this component's HTML rendering path.
export function LegalDocument({ slug }: { slug: LegalSlug }) {
  const document = legalDocuments[slug]
  return (
    <article className="legal-content legal-document" aria-labelledby="legal-title">
      <header className="legal-intro">
        <p className="eyebrow">Konvertira legal information</p>
        <h1 id="legal-title">{document.title}</h1>
        <p className="legal-updated">Draft revision: {document.updated}</p>
        <p>{document.summary}</p>
      </header>
      <aside className="legal-note" aria-label="Pre-publication requirements"><p>{document.reviewNotice}</p></aside>
      <nav className="legal-toc" aria-label="Table of contents">
        <h2>Contents</h2>
        <ol>{document.sections.map((section) => <li key={section.id}><a href={`#${section.id}`}>{section.title}</a></li>)}</ol>
      </nav>
      {document.sections.map((section) => (
        <section key={section.id} aria-labelledby={section.id}>
          <h2 id={section.id}>{section.title}</h2>
          <div dangerouslySetInnerHTML={{ __html: section.body.join('\n') }} />
        </section>
      ))}
      <nav className="legal-related" aria-label="Related legal pages">
        <a href="/terms">Terms of Service</a>
        <a href="/privacy">Privacy Policy</a>
        <a href="/security">Security &amp; Data Handling</a>
        <a href="/support">Support</a>
        <a href="/about">About</a>
      </nav>
    </article>
  )
}
