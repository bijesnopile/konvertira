import { Link } from 'react-router-dom'
import logoUrl from '../assets/ikona.png'

interface LogoProps {
  light?: boolean
}

export function Logo({ light = false }: LogoProps) {
  return (
    <Link to="/" className="group inline-flex items-center gap-2.5 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-500 focus-visible:ring-offset-4" aria-label="Konvertira home">
      <img
        src={logoUrl}
        alt=""
        width="40"
        height="40"
        className="h-10 w-10 shrink-0 rounded-xl object-contain shadow-sm"
      />
      <span className={`text-xl font-semibold tracking-tight ${light ? 'text-white' : 'text-ink'}`}>Konvertira</span>
    </Link>
  )
}
