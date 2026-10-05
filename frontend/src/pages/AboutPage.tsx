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
              <p className="mt-4 leading-7 text-slate-600">The first release focuses on useful image tasks: converting between JPG, PNG, and WEBP, and creating fresh image copies without intentionally carrying over common embedded metadata.</p>
              <p className="mt-4 leading-7 text-slate-600">The project is still small and independently operated. Some limits are necessary, but the long-term goal is to support more formats, larger files, and more privacy-focused tools while keeping the service understandable and accessible.</p>
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
            <h2 className="text-2xl font-semibold text-ink">Try the local image tools</h2>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-600">Your supported image stays on your device from selection to download.</p>
            <Link to="/#tools" className="button-primary mt-6">Choose an image</Link>
          </div>
        </div>
      </section>
    </>
  )
}
