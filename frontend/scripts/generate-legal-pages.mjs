import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const escape = (value) => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#x27;')
const related = '<a href="/terms">Terms of Service</a><a href="/privacy">Privacy Policy</a><a href="/security">Security &amp; Data Handling</a><a href="/support">Support</a><a href="/about">About</a>'

// Deterministic, build-time generation from trusted checked-in copy. No network,
// user data or JavaScript is included in the generated public documents.
for (const slug of ['privacy', 'terms', 'security']) {
  const document = JSON.parse(readFileSync(new URL(`../src/legal/${slug}.json`, import.meta.url), 'utf8'))
  const article = `<article class="legal-content legal-document" aria-labelledby="legal-title">
<header class="legal-intro"><p class="eyebrow">Konvertira legal information</p><h1 id="legal-title">${escape(document.title)}</h1><p class="legal-updated">Draft revision: ${escape(document.updated)}</p><p>${escape(document.summary)}</p></header>
<aside class="legal-note" aria-label="Pre-publication requirements"><p>${escape(document.reviewNotice)}</p></aside>
<nav class="legal-toc" aria-label="Table of contents"><h2>Contents</h2><ol>${document.sections.map((section) => `<li><a href="#${escape(section.id)}">${escape(section.title)}</a></li>`).join('')}</ol></nav>
${document.sections.map((section) => `<section aria-labelledby="${escape(section.id)}"><h2 id="${escape(section.id)}">${escape(section.title)}</h2><div>${section.body.join('\n')}</div></section>`).join('\n')}
<nav class="legal-related" aria-label="Related legal pages">${related}</nav>
</article>`
  const html = `<!doctype html>
<!-- Generated from src/legal/${slug}.json by npm run legal:generate. Edit the source, not this copy. -->
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="${escape(document.summary)}">
  <meta name="theme-color" content="#f7f6f1">
  <link rel="canonical" href="https://konvertira.com/${slug}">
  <link rel="stylesheet" href="/legal.css">
  <title>${escape(document.title)} — Konvertira</title>
</head>
<body>
  <a class="legal-skip" href="#main-content">Skip to content</a>
  <header class="site-header"><a class="brand" href="/">Konvertira<span>Independent file tools</span></a><nav aria-label="Main navigation"><a href="/convert">Convert</a>${related}</nav></header>
  <main id="main-content" tabindex="-1">${article}</main>
  <footer class="site-footer"><a href="/">Konvertira</a><nav aria-label="Footer navigation">${related}</nav></footer>
</body>
</html>
`
  const path = new URL(`../public/${slug}.html`, import.meta.url)
  if (process.argv.includes('--check')) {
    if (readFileSync(path, 'utf8').replaceAll('\r\n', '\n') !== html) {
      throw new Error(`Stale legal document: ${fileURLToPath(path)}. Run npm run legal:generate.`)
    }
  } else {
    writeFileSync(path, html)
  }
}
