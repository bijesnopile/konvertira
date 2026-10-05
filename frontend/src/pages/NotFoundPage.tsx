import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section className="grid min-h-[65vh] place-items-center px-5 py-20 text-center">
      <div><p className="eyebrow">404</p><h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink">Page not found</h1><p className="mt-4 text-slate-600">The page you’re looking for doesn’t exist.</p><Link to="/" className="button-primary mt-7">Back to homepage</Link></div>
    </section>
  )
}
