import { Link } from 'react-router-dom'
import { ToolCard } from '../components/ToolCard'

const features = [
  {
    title: 'Remove metadata',
    description: 'Strip GPS, camera details, capture dates, and other embedded image data.',
    icon: <><path d="M12 3 5 6v5c0 4.6 2.8 8.5 7 10 4.2-1.5 7-5.4 7-10V6l-7-3Z" /><path d="m9 12 2 2 4-4" /></>,
  },
  {
    title: 'Convert images',
    description: 'Move between JPG, PNG, and WEBP with a simple, focused workflow.',
    icon: <><path d="M7 7h11l-3-3" /><path d="m18 7-3 3" /><path d="M17 17H6l3 3" /><path d="m6 17 3-3" /></>,
  },
  {
    title: 'Privacy-focused processing',
    description: 'Files are processed only to perform the operation you request.',
    icon: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  },
  {
    title: 'More file types soon',
    description: 'Useful tools for documents, presentations, and spreadsheets are next.',
    icon: <><path d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" /><path d="M14 3v5h5" /><path d="M9 13h6M9 17h4" /></>,
  },
]

const upcoming = ['PDF metadata removal', 'PDF to image', 'DOCX to PDF', 'XLSX to PDF', 'PPTX to PDF', 'Metadata inspection']

export function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden px-5 pb-16 pt-20 text-center sm:px-8 sm:pb-20 sm:pt-28 lg:px-10">
        <div className="hero-grid absolute inset-0 opacity-50" aria-hidden="true" />
        <div className="relative mx-auto max-w-4xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-forest-200 bg-white px-3.5 py-2 text-xs font-semibold text-forest-800 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-forest-500" />
            Private by design. Simple by default.
          </div>
          <h1 className="text-balance text-4xl font-semibold tracking-[-0.04em] text-ink sm:text-6xl lg:text-7xl">
            Convert files. Remove metadata. <span className="text-forest-700">Keep control.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-pretty text-base leading-7 text-slate-600 sm:text-lg sm:leading-8">
            Konvertira helps you convert files and remove sensitive metadata such as GPS, EXIF, camera information and other embedded data.
          </p>
          <div className="mt-9 flex flex-col items-center gap-3">
            <Link to="/#tools" className="button-primary px-7 py-3.5 text-base">
              Choose a file
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></svg>
            </Link>
            <span className="text-sm text-slate-500">No account required</span>
          </div>
        </div>
      </section>

      <ToolCard />

      <section id="privacy" className="bg-forest-900 px-5 py-20 text-white sm:px-8 sm:py-28 lg:px-10">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:gap-20">
          <div>
            <p className="eyebrow text-forest-300">Your data, respected</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">Privacy comes first</h2>
            <p className="mt-5 max-w-xl text-base leading-7 text-white/65 sm:text-lg">A practical file tool should do its job without turning your files into a product. Our processing is designed around that principle.</p>
            <Link to="/privacy" className="mt-7 inline-flex items-center gap-2 rounded-lg text-sm font-semibold text-white underline decoration-white/30 underline-offset-4 hover:decoration-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-4 focus-visible:ring-offset-forest-900">
              Read our privacy policy <span aria-hidden="true">→</span>
            </Link>
          </div>
          <div className="grid gap-px overflow-hidden rounded-2xl bg-white/10 sm:grid-cols-2">
            <PrivacyPoint number="01" text="Files are processed only for the operation you request." />
            <PrivacyPoint number="02" text="Processed files are temporary and scheduled for deletion." />
            <PrivacyPoint number="03" text="Remove GPS location and camera information from images." />
            <PrivacyPoint number="04" text="Clean capture dates and embedded application metadata." />
          </div>
        </div>
      </section>

      <section className="px-5 py-20 sm:px-8 sm:py-28 lg:px-10" aria-labelledby="features-heading">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-2xl">
            <p className="eyebrow">Built for the task</p>
            <h2 id="features-heading" className="mt-4 text-3xl font-semibold tracking-tight text-ink sm:text-5xl">Simple tools, thoughtful handling</h2>
          </div>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <article key={feature.title} className="rounded-2xl border border-black/[0.07] bg-white p-6 shadow-sm">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-forest-100 text-forest-800" aria-hidden="true">
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{feature.icon}</svg>
                </span>
                <h3 className="mt-5 font-semibold text-ink">{feature.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{feature.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-black/[0.06] bg-white px-5 py-20 sm:px-8 sm:py-28 lg:px-10" aria-labelledby="coming-soon-heading">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div><p className="eyebrow">What’s next</p><h2 id="coming-soon-heading" className="mt-4 text-3xl font-semibold tracking-tight text-ink sm:text-5xl">More useful tools are on the way</h2></div>
            <span className="w-fit rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-amber-800">Coming soon</span>
          </div>
          <ul className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {upcoming.map((item) => (
              <li key={item} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50/70 px-5 py-4 text-sm font-semibold text-slate-600" aria-disabled="true">
                {item}
                <svg viewBox="0 0 24 24" className="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  )
}

function PrivacyPoint({ number, text }: { number: string; text: string }) {
  return <div className="bg-forest-900 p-6 sm:p-7"><span className="text-xs font-semibold tracking-widest text-forest-300">{number}</span><p className="mt-3 text-sm leading-6 text-white/80">{text}</p></div>
}
