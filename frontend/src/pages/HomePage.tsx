import { Link } from 'react-router-dom'
import { ProcessingModeBadge, ProcessingModeInfo } from '../components/ProcessingMode'
import { ToolCard } from '../components/ToolCard'

const features = [
  {
    title: 'Image conversion',
    description: 'Convert, resize, and compress common images locally, or use clearly labeled server codecs for HEIC, AVIF, and static GIF.',
    href: '/convert',
    icon: <><path d="M12 3 5 6v5c0 4.6 2.8 8.5 7 10 4.2-1.5 7-5.4 7-10V6l-7-3Z" /><path d="m9 12 2 2 4-4" /></>,
  },
  {
    title: 'PDF tools',
    description: 'Merge, split, reorder, extract, rasterize, create, optimize, and inspect PDFs with bounded server processing.',
    href: '/pdf-tools',
    icon: <><path d="M7 7h11l-3-3" /><path d="m18 7-3 3" /><path d="M17 17H6l3 3" /><path d="m6 17 3-3" /></>,
  },
  {
    title: 'Metadata privacy',
    description: 'Inspect supported metadata and create cleaned copies without claiming anonymity, redaction, or malware removal.',
    href: '/metadata',
    icon: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  },
  {
    title: 'Documents and Office',
    description: 'Convert supported documents, spreadsheets, and presentations with honest fidelity warnings.',
    href: '/convert',
    icon: <><path d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" /><path d="M14 3v5h5" /><path d="M9 13h6M9 17h4" /></>,
  },
]

export function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden px-5 pb-16 pt-20 text-center sm:px-8 sm:pb-20 sm:pt-28 lg:px-10">
        <div className="hero-grid absolute inset-0 opacity-50" aria-hidden="true" />
        <div className="relative mx-auto max-w-4xl">
          <div className="mb-6"><ProcessingModeBadge mode="local" label="Image tools process locally" /></div>
          <h1 className="text-balance text-4xl font-semibold tracking-[-0.04em] text-ink sm:text-6xl lg:text-7xl">
            Convert files. Remove metadata. <span className="text-forest-700">Keep control.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-pretty text-base leading-7 text-slate-600 sm:text-lg sm:leading-8">
            Use local image tools without uploading, or choose clearly labeled server tools for PDF, document, spreadsheet, presentation, and advanced image workflows.
          </p>
          <div className="mt-9 flex flex-col items-center gap-3">
            <Link to="/#tools" className="button-primary px-7 py-3.5 text-base">
              Choose a file
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></svg>
            </Link>
            <span className="text-sm text-slate-500">No account required · Processing mode shown before you start</span>
          </div>
        </div>
      </section>

      <ToolCard />

      <section id="privacy" className="bg-forest-900 px-5 py-20 text-white sm:px-8 sm:py-28 lg:px-10">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:gap-20">
          <div>
            <p className="eyebrow text-forest-300">Clear by default</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">Privacy by design</h2>
            <p className="mt-5 max-w-xl text-base leading-7 text-white/70 sm:text-lg">For supported local image tools, your browser does the work and the image does not reach our server. Tools that require an upload are labeled as server processing before you select or submit a file.</p>
            <Link to="/privacy" className="mt-7 inline-flex items-center gap-2 rounded-lg text-sm font-semibold text-white underline decoration-white/30 underline-offset-4 hover:decoration-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-4 focus-visible:ring-offset-forest-900">
              Read our privacy policy <span aria-hidden="true">→</span>
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <ProcessingModeInfo
              mode="local"
              title="Images"
              description="JPG, PNG, and static WEBP conversion and metadata removal run on your device."
              className="h-full"
            >
              <ul className="mt-5 space-y-2 text-sm text-slate-600">
                <ModeItem>Conversion in your browser</ModeItem>
                <ModeItem>Metadata-clean re-encoding</ModeItem>
                <ModeItem>No upload required</ModeItem>
              </ul>
            </ProcessingModeInfo>
            <ProcessingModeInfo
              mode="server"
              title="Server workflows"
              description="PDFs, documents, advanced image codecs, Office files, and MCP workflows use server infrastructure."
              className="h-full"
            >
              <ul className="mt-5 space-y-2 text-sm text-slate-600">
                <ModeItem>Clearly indicated before upload</ModeItem>
                <ModeItem>Used only for the requested task</ModeItem>
                <ModeItem>Temporary processing</ModeItem>
              </ul>
            </ProcessingModeInfo>
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
              <Link key={feature.title} to={feature.href} className="rounded-2xl border border-black/[0.07] bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-forest-300">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-forest-100 text-forest-800" aria-hidden="true">
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{feature.icon}</svg>
                </span>
                <h3 className="mt-5 font-semibold text-ink">{feature.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{feature.description}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-black/[0.06] bg-white px-5 py-20 sm:px-8 sm:py-28 lg:px-10" aria-labelledby="tools-overview-heading">
        <div className="mx-auto max-w-7xl">
          <p className="eyebrow">Available now</p>
          <h2 id="tools-overview-heading" className="mt-4 text-3xl font-semibold tracking-tight text-ink sm:text-5xl">Choose the right tool and processing mode</h2>
          <p className="mt-5 max-w-2xl text-sm leading-6 text-slate-600">Local tools never fall back to an upload. Server tools are bounded by file, page, pixel, concurrency, timeout, and temporary-storage limits.</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link to="/convert" className="button-primary">All converters</Link>
            <Link to="/pdf-tools" className="button-secondary">PDF toolkit</Link>
            <Link to="/metadata" className="button-secondary">Metadata tools</Link>
          </div>
        </div>
      </section>
    </>
  )
}

function ModeItem({ children }: { children: string }) {
  return <li className="flex gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-forest-500" aria-hidden="true" /><span>{children}</span></li>
}
