import { Outlet, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'

const pageMetadata: Record<string, { title: string; description: string }> = {
  '/': { title: 'Konvertira — Privacy-focused file conversion', description: 'Privacy-focused image, PDF, document, spreadsheet, presentation, and metadata tools with clearly labeled local and server processing.' },
  '/convert': { title: 'File converters — Konvertira', description: 'Convert supported images, documents, spreadsheets, and presentations with clear local or server processing labels.' },
  '/pdf-tools': { title: 'PDF tools — Konvertira', description: 'Merge, split, reorder, extract, rasterize, create, optimize, and inspect PDFs with bounded server processing.' },
  '/metadata': { title: 'Metadata privacy tools — Konvertira', description: 'Inspect supported file metadata and create a cleaned copy with explicit privacy limitations.' },
  '/privacy': { title: 'Privacy Policy — Konvertira', description: 'Konvertira personal-data handling, local and server processing, retention, legal bases and privacy rights.' },
  '/terms': { title: 'Terms of Service — Konvertira', description: 'Terms for using Konvertira file conversion and metadata tools, with mandatory consumer rights preserved.' },
  '/security': { title: 'Security & Data Handling — Konvertira', description: 'Konvertira processing boundaries, implemented security controls and operational limitations.' },
  '/support': { title: 'Support — Konvertira', description: 'Get help with Konvertira formats, limits, privacy, and technical issues.' },
  '/about': { title: 'About — Konvertira', description: 'About Konvertira, an independent privacy-focused file tools project.' },
}

export function Layout() {
  const { pathname, hash } = useLocation()

  useEffect(() => {
    if (hash) {
      requestAnimationFrame(() => document.querySelector(hash)?.scrollIntoView({ behavior: 'smooth' }))
    } else {
      window.scrollTo({ top: 0 })
    }
  }, [pathname, hash])

  useEffect(() => {
    const metadata = pageMetadata[pathname] ?? { title: 'Page not found — Konvertira', description: 'The requested Konvertira page could not be found.' }
    document.title = metadata.title
    document.querySelector<HTMLMetaElement>('meta[name="description"]')?.setAttribute('content', metadata.description)
    document.querySelector<HTMLMetaElement>('meta[property="og:title"]')?.setAttribute('content', metadata.title)
    document.querySelector<HTMLMetaElement>('meta[property="og:description"]')?.setAttribute('content', metadata.description)
    document.querySelector<HTMLMetaElement>('meta[name="twitter:title"]')?.setAttribute('content', metadata.title)
    document.querySelector<HTMLMetaElement>('meta[name="twitter:description"]')?.setAttribute('content', metadata.description)
    const canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]')
    canonical?.setAttribute('href', `https://konvertira.com${pathname === '/' ? '/' : pathname}`)
    document.querySelector<HTMLMetaElement>('meta[property="og:url"]')?.setAttribute('content', canonical?.href ?? 'https://konvertira.com/')
  }, [pathname])

  return (
    <div className="flex min-h-screen flex-col bg-sand">
      <Header />
      <main className="flex-1"><Outlet /></main>
      <Footer />
    </div>
  )
}
