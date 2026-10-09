import { Link } from 'react-router-dom'
import { Logo } from './Logo'

export function Footer() {
  return (
    <footer className="bg-forest-900 text-white">
      <div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:px-10">
        <div className="flex flex-col justify-between gap-10 border-b border-white/10 pb-10 sm:flex-row sm:items-start">
          <div className="max-w-sm">
            <Logo light />
            <p className="mt-4 text-sm leading-6 text-white/65">Independent file tools with local image processing and clear server-use labels.</p>
          </div>
          <nav className="grid grid-cols-2 gap-x-12 gap-y-3 text-sm sm:grid-cols-3" aria-label="Footer navigation">
            <Link className="footer-link" to="/convert">Convert</Link>
            <Link className="footer-link" to="/pdf-tools">PDF tools</Link>
            <Link className="footer-link" to="/metadata">Metadata</Link>
            <Link className="footer-link" to="/privacy">Privacy</Link>
            <Link className="footer-link" to="/terms">Terms</Link>
            <Link className="footer-link" to="/support">Support</Link>
            <Link className="footer-link" to="/about">About</Link>
            <a className="footer-link" href="https://github.com/bijesnopile/konvertira" target="_blank" rel="noopener noreferrer">GitHub</a>
          </nav>
        </div>
        <div className="flex flex-col gap-2 pt-7 text-sm text-white/50 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Konvertira. All rights reserved.</p>
          <p>konvertira.com</p>
        </div>
      </div>
    </footer>
  )
}
