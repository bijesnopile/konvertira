import { Link } from 'react-router-dom'

interface LogoProps {
  light?: boolean
}

export function Logo({ light = false }: LogoProps) {
  return (
    <Link to="/" className="group inline-flex items-center gap-2.5 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-500 focus-visible:ring-offset-4" aria-label="Konvertira home">
      <span className={`grid h-9 w-9 place-items-center rounded-xl transition-transform group-hover:-rotate-3 ${light ? 'bg-white text-forest-800' : 'bg-forest-800 text-white'}`} aria-hidden="true">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 4v16M17 5 9 12l8 7" />
        </svg>
      </span>
      <span className={`text-xl font-semibold tracking-tight ${light ? 'text-white' : 'text-ink'}`}>Konvertira</span>
    </Link>
  )
}
