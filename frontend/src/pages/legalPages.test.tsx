import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { Footer } from '../components/Footer'
import { legalDocuments } from '../legal/LegalDocument'
import { PrivacyPage } from './PrivacyPage'
import { TermsPage } from './TermsPage'
import { SecurityPage } from './SecurityPage'
import { SupportPage } from './SupportPage'

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8')
const nginx = read('../../nginx.conf')
const text = (html: string) => html.replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim()
const article = (html: string) => html.slice(html.indexOf('<article'), html.lastIndexOf('</article>') + '</article>'.length)
const ids = (html: string) => [...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1])
const hrefs = (html: string) => [...html.matchAll(/\bhref="([^"]+)"/g)].map((match) => match[1])
const app = read('../App.tsx')
const routes = new Set(['/', ...[...app.matchAll(/path="(\/[^"#]*)"/g)].map((match) => match[1])])
const pages = [
  ['privacy', PrivacyPage, 'Privacy Policy'],
  ['terms', TermsPage, 'Terms of Service'],
  ['security', SecurityPage, 'Security &amp; Data Handling'],
  ['support', SupportPage, 'Contact support'],
] as const

describe('crawler-readable legal pages', () => {
  for (const [page, Component, expected] of pages) {
    it(`${page} serves complete, matching static content without JavaScript`, () => {
      const html = read(`../../public/${page}.html`)
      expect(html).toContain(expected)
      expect(html).toContain('legal@konvertira.com')
      expect(html).toContain(`https://konvertira.com/${page}`)
      expect(html).toContain('href="/legal.css"')
      expect(html).not.toMatch(/<script\b|<style\b|\sstyle=|\son\w+=/i)
      // All article copy, lists, table cells, link destinations and IDs are compared.
      const react = renderToStaticMarkup(<Component />)
      expect(text(article(html))).toEqual(text(article(react)))
      expect(hrefs(article(html))).toEqual(hrefs(article(react)))
      expect(ids(article(html))).toEqual(ids(article(react)))
      expect(html).toContain('<html lang="en">')
      expect(html).toContain('name="viewport" content="width=device-width, initial-scale=1"')
      expect(html.match(/<h1\b/g)).toHaveLength(1)
      expect(html).toMatch(/<main\b/)
      expect(html).toMatch(/<article\b/)
      expect(html).toContain('aria-label="Footer navigation"')
    })

    it(`${page} has an exact static Nginx route, no SPA fallback, and all security headers`, () => {
      const block = nginx.match(new RegExp(`location = /${page} \\{([\\s\\S]*?)\\n    \\}`))?.[1]
      expect(block).toBeDefined()
      expect(block).toContain(`try_files /${page}.html =404;`)
      expect(block).not.toContain('index.html')
      expect(block).toContain('add_header Cache-Control "no-cache";')
      const existing = nginx.match(/location \/ \{([\s\S]*?)\n    \}/)?.[1] || ''
      const security = [...existing.matchAll(/add_header (?!Cache-Control)[^\n]+/g)].map((match) => match[0].trim())
      expect(security).toHaveLength(7)
      for (const header of security) expect(block).toContain(header)
    })

    it(`${page} has valid internal navigation and a security link`, () => {
      const html = read(`../../public/${page}.html`)
      const pageIds = ids(html)
      expect(new Set(pageIds).size).toBe(pageIds.length)
      for (const href of hrefs(html)) {
        if (href.startsWith('#')) expect(pageIds).toContain(href.slice(1))
        else if (href.startsWith('/') && href !== '/legal.css') expect(routes.has(href)).toBe(true)
      }
      expect(hrefs(html)).toContain('/security')
      expect(hrefs(html)).toContain('/support')
      expect(hrefs(html)).toContain('/about')
    })
  }

  for (const [slug, document] of Object.entries(legalDocuments)) {
    it(`${slug} has a complete linked contents list and explicitly labelled review requirements`, () => {
      const html = read(`../../public/${slug}.html`)
      expect(html).toContain('aria-label="Table of contents"')
      expect(html).toContain('PRE-PUBLICATION')
      expect(html).toContain('Draft revision: October 11, 2026')
      expect(html).not.toMatch(/\b(?:TODO|TBD|Lorem ipsum|INSERT ADDRESS|YOUR COMPANY)\b/)
      const toc = html.match(/<nav class="legal-toc"[\s\S]*?<\/nav>/)?.[0] ?? ''
      expect(hrefs(toc)).toEqual(document.sections.map((section) => `#${section.id}`))
      for (const section of document.sections) {
        expect(html).toContain(`aria-labelledby="${section.id}"`)
        expect(html).toContain(`id="${section.id}"`)
        // Body markup is policy-author controlled. Allow only the required semantic
        // subset so a future edit cannot introduce executable or embedded content.
        const body = section.body.join('\n')
        const allowed = new Set(['p', 'a', 'div', 'table', 'caption', 'thead', 'tbody', 'tr', 'th', 'td', 'ul', 'ol', 'li', 'strong', 'em', 'h3'])
        for (const tag of body.matchAll(/<\/?([a-z0-9]+)\b/gi)) expect(allowed.has(tag[1])).toBe(true)
        expect(body).not.toMatch(/\son\w+=|\sstyle=|javascript:|data:|<script/i)
      }
    })
  }

  it('keeps substantive documents within their requested approximate scope', () => {
    for (const [slug, minimum, maximum] of [['terms', 2500, 4400], ['privacy', 2500, 4400], ['security', 1500, 2800]] as const) {
      const document = legalDocuments[slug]
      const count = text(document.sections.map((section) => section.body.join(' ')).join(' ')).split(/\s+/).length
      expect(count).toBeGreaterThanOrEqual(minimum)
      expect(count).toBeLessThanOrEqual(maximum)
    }
  })

  it('detects stale generated pages without modifying files', () => {
    expect(() => execFileSync(process.execPath, [fileURLToPath(new URL('../../scripts/generate-legal-pages.mjs', import.meta.url)), '--check'])).not.toThrow()
  })

  it('preserves GDPR, consumer and retention limitations rather than claiming compliance', () => {
    const privacy = text(read('../../public/privacy.html'))
    for (const phrase of ['Article 6(1)(b)', 'Article 6(1)(f)', 'Article 6(1)(c)', 'Article 6(1)(a)', 'Article 9', 'Article 14', 'Chapter V', 'one month', 'AZOP', 'approximately 15 minutes', 'not a blanket basis', 'not an exact-second', 'not a legal opinion']) expect(privacy).toContain(phrase)
    const terms = text(read('../../public/terms.html'))
    for (const phrase of ['gross negligence', 'intentional misconduct', 'mandatory consumer', 'not required', 'no consumer indemnity', 'Croatia']) expect(terms).toContain(phrase)
    expect(terms).not.toMatch(/EUR\s*(0|100)\b|class-action waiver|waive all rights/)
  })

  it('describes safeguards with explicit qualifications, not unsupported certifications', () => {
    const security = text(read('../../public/security.html'))
    for (const phrase of ['does not claim end-to-end encryption', 'not a complete network sandbox', 'not a separate virtual machine', 'not represented here as an entirely non-root', 'not a network configured', 'CPUExecutionProvider', 'SHA-256', 'not trained', 'No bug bounty', 'no claim of EEA-only']) expect(security.toLowerCase()).toContain(phrase.toLowerCase())
    expect(security).not.toMatch(/(?:we are|Konvertira is) (?:ISO|SOC|PCI|certified|audited)|guaranteed anonymity/i)
    expect(security).toContain('Not every HTTP operation')
  })

  it('makes retention tables accessible and contains overflow on small screens', () => {
    const privacy = read('../../public/privacy.html')
    expect(privacy).toContain('<caption>')
    expect(privacy.match(/scope="col"/g)).toHaveLength(5)
    expect(privacy).toContain('scope="row"')
    expect(privacy).toContain('role="region" aria-label="Processing and retention table" tabindex="0"')
    const css = read('../../public/legal.css')
    expect(css).toContain('overflow-x: auto')
    expect(css).toContain('max-width: 100%')
    expect(css).toContain(':focus-visible')
    expect(css).toContain('max-width: 40rem')
    expect(css).toContain('prefers-reduced-motion')
    expect(css).not.toContain('color-scheme: dark') // Existing site is light-only.
  })

  it('links security in the React footer, metadata and sitemap without changing robots', () => {
    const footer = renderToStaticMarkup(<MemoryRouter><Footer /></MemoryRouter>)
    for (const route of ['/terms', '/privacy', '/security', '/support', '/about']) expect(hrefs(footer)).toContain(route)
    expect(read('../components/Layout.tsx')).toContain("'/security': { title: 'Security & Data Handling — Konvertira'")
    expect(read('../../public/sitemap.xml')).toContain('<loc>https://konvertira.com/security</loc>')
    expect(read('../../public/robots.txt')).toContain('Allow: /')
  })

  it('copies the Vite build and Nginx configuration from the correct Docker paths', () => {
    const docker = read('../../Dockerfile')
    expect(docker).toContain('COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf')
    expect(docker).toContain('COPY --from=build /app/frontend/dist /usr/share/nginx/html')
  })
})
