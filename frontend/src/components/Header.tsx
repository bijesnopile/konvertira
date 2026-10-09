import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Logo } from './Logo'

const navItems = [
  { label: 'Convert', href: '/convert' },
  { label: 'PDF', href: '/pdf-tools' },
  { label: 'Metadata', href: '/metadata' },
  { label: 'Privacy', href: '/privacy' },
  { label: 'About', href: '/about' },
]

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  return (
    <header className="sticky top-0 z-50 border-b border-black/[0.06] bg-sand/90 backdrop-blur-xl">
      <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
        <Logo />

        <nav className="hidden items-center gap-8 md:flex" aria-label="Main navigation">
          {navItems.map((item) => {
            const active = location.pathname === item.href
            return (
              <Link key={item.href} to={item.href} className={`nav-link ${active ? 'text-forest-800' : ''}`} aria-current={active ? 'page' : undefined}>
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="hidden md:block">
          <Link to="/convert" className="button-primary px-5 py-2.5 text-sm">Start converting</Link>
        </div>

        <button
          type="button"
          className="grid h-11 w-11 place-items-center rounded-xl text-ink hover:bg-white focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-500 md:hidden"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-controls="mobile-navigation"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
        >
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {menuOpen ? <><path d="m6 6 12 12" /><path d="M18 6 6 18" /></> : <><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></>}
          </svg>
        </button>
      </div>

      {menuOpen && (
        <nav id="mobile-navigation" className="border-t border-black/[0.06] bg-sand px-5 py-5 md:hidden" aria-label="Mobile navigation">
          <div className="mx-auto flex max-w-7xl flex-col gap-1">
            {navItems.map((item) => (
              <Link key={item.href} to={item.href} onClick={() => setMenuOpen(false)} className="rounded-lg px-3 py-3 font-medium text-ink hover:bg-white focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-500">
                {item.label}
              </Link>
            ))}
            <Link to="/convert" onClick={() => setMenuOpen(false)} className="button-primary mt-3 w-full">Start converting</Link>
          </div>
        </nav>
      )}
    </header>
  )
}
