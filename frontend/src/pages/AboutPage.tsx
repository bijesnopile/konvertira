import { Link } from 'react-router-dom'
import { PageIntro } from '../components/PageIntro'
import { ProcessingModeInfo } from '../components/ProcessingMode'

export function AboutPage() {
  return (
    <>
      <PageIntro eyebrow="About Konvertira" title="A small project with a practical purpose.">
        Simple file tools should not require a subscription, an unnecessary account, or unclear handling of your files.
      </PageIntro>

      <section className="px-5 py-16 sm:px-8 sm:py-24">
        <div className="mx-auto max-w-4xl">
          <div className="grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:gap-20">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-ink">Why Konvertira exists</h2>
              <p className="mt-4 leading-7 text-slate-600">Konvertira started as a side project by a student who was tired of simple file conversions being locked behind subscriptions, unnecessary sign-ups, or confusing limits.</p>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <p className="leading-7 text-slate-600">Konvertira is developed by <span className="font-semibold text-ink">Matej Tokić</span>.</p>
                <a href="https://x.com/t0kic_" target="_blank" rel="noopener noreferrer" aria-label="Matej Tokić on X" className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-ink transition-colors hover:bg-forest-50 hover:text-forest-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-500 focus-visible:ring-offset-2">
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor" aria-hidden="true"><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.64 7.584H.47l8.6-9.835L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z" /></svg>
                </a>
              </div>
              <p className="mt-4 leading-7 text-slate-600">Today it includes local JPG, PNG, and static WEBP workflows plus clearly labeled server tools for advanced images, PDFs, documents, spreadsheets, presentations, and supported metadata.</p>
              <p className="mt-4 leading-7 text-slate-600">The project is still small and independently operated. File, page, pixel, time, concurrency, and temporary-storage limits keep it practical on modest infrastructure while the service remains understandable and accessible.</p>
            </div>

            <aside className="rounded-3xl bg-forest-900 p-8 text-white">
              <p className="text-sm font-semibold uppercase tracking-widest text-forest-300">Built around</p>
              <ul className="mt-6 space-y-5 text-sm leading-6 text-white/75">
                <li className="flex gap-3"><span className="text-forest-300">01</span><span>Local processing whenever it is practical and reliable.</span></li>
                <li className="flex gap-3"><span className="text-forest-300">02</span><span>Clear notice before a tool needs server infrastructure.</span></li>
                <li className="flex gap-3"><span className="text-forest-300">03</span><span>No account requirement for basic image tools.</span></li>
                <li className="flex gap-3"><span className="text-forest-300">04</span><span>Plain explanations instead of exaggerated privacy claims.</span></li>
              </ul>
            </aside>
          </div>

          <div className="mt-16 grid gap-4 sm:grid-cols-2">
            <ProcessingModeInfo
              mode="local"
              title="Common image tools"
              description="Supported image conversion and metadata removal happen directly in your browser without uploading the image."
            />
            <ProcessingModeInfo
              mode="server"
              title="Tools that need more"
              description="PDF, document, unsupported-format, and MCP workflows may use server processing and will be clearly identified."
            />
          </div>

          <div className="mt-16 border-t border-black/10 pt-10 text-center">
            <h2 className="text-2xl font-semibold text-ink">Explore or contribute</h2>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-600">Try a supported tool, or visit the public repository to follow development and report technical issues.</p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link to="/convert" className="button-primary">Explore converters</Link>
              <a href="https://github.com/bijesnopile/konvertira" target="_blank" rel="noopener noreferrer" className="button-secondary">View on GitHub</a>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
