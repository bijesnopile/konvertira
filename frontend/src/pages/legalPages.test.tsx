import { readFileSync } from 'node:fs'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { PrivacyPage } from './PrivacyPage'
import { TermsPage } from './TermsPage'
import { SupportPage } from './SupportPage'

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8')
const nginx = read('../../nginx.conf')
const text = (html: string) => html.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim()
const policyContent = (html: string) => {
  const article = html.slice(html.indexOf('<article'), html.lastIndexOf('</article>'))
  return [...article.matchAll(/<(p|h2)\b[^>]*>([\s\S]*?)<\/\1>/g)].map((match) => text(match[2]))
}

describe('crawler-readable legal pages', () => {
  for (const [page, Component, expected] of [
    ['privacy', PrivacyPage, 'Privacy philosophy'],
    ['terms', TermsPage, 'Terms of service'],
    ['support', SupportPage, 'Contact support'],
  ] as const) {
    it(`${page} preserves the React policy text without requiring JavaScript`, () => {
      const html = read(`../../public/${page}.html`)
      expect(html).toContain(expected)
      expect(html).toContain('legal@konvertira.com')
      expect(html).toContain(`https://konvertira.com/${page}`)
      expect(html).toContain('href="/legal.css"')
      expect(html).not.toMatch(/<script\b|<style\b|\sstyle=|\son\w+=/i)
      expect(policyContent(html)).toEqual(policyContent(renderToStaticMarkup(<Component />)))
    })

    it(`${page} has an exact static Nginx route with the existing security headers`, () => {
      const block = nginx.match(new RegExp(`location = /${page} \\{([\\s\\S]*?)\\n    \\}`))?.[1]
      expect(block).toBeDefined()
      expect(block).toContain(`try_files /${page}.html =404;`)
      expect(block).toContain('add_header Cache-Control "no-cache";')
      const existing = nginx.match(/location \/ \{([\s\S]*?)\n    \}/)?.[1] || ''
      const security = [...existing.matchAll(/add_header (?!Cache-Control)[^\n]+/g)].map((match) => match[0].trim())
      expect(security).toHaveLength(7)
      for (const header of security) expect(block).toContain(header)
    })
  }

  it('preserves bounded retention and privacy limitations in the raw response content', () => {
    const html = read('../../public/privacy.html')
    for (const phrase of ['approximately 15 minutes', 'different bounded retention period', 'does not claim immediate deletion', 'guaranteed anonymization', 'every conceivable privacy artifact', 'Third-party infrastructure', 'ChatGPT', 'MCP']) {
      expect(html).toContain(phrase)
    }
  })

  it('copies the Vite build and Nginx configuration from their actual Docker paths', () => {
    const docker = read('../../Dockerfile')
    expect(docker).toContain('COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf')
    expect(docker).toContain('COPY --from=build /app/frontend/dist /usr/share/nginx/html')
  })
})
