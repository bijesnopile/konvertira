import { Link } from 'react-router-dom'
import { PageIntro } from '../components/PageIntro'

export function AboutPage() {
  return (
    <>
      <PageIntro eyebrow="About Konvertira" title="Useful file tools, with fewer compromises.">
        Konvertira is a privacy-first file conversion and metadata cleaning service built to make everyday file tasks clear and dependable.
      </PageIntro>
      <section className="px-5 py-16 sm:px-8 sm:py-24">
        <div className="mx-auto grid max-w-4xl gap-12 lg:grid-cols-2 lg:gap-20">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-ink">Why we’re building it</h2>
            <p className="mt-4 leading-7 text-slate-600">Files often carry more information than people realize. A photo can contain where and when it was taken, what device captured it, and which software edited it. Konvertira makes it easier to remove that information and convert files without a complicated workflow.</p>
            <p className="mt-4 leading-7 text-slate-600">The first release focuses on JPG, PNG, and WEBP images. Future tools will expand to PDFs and common office document formats.</p>
          </div>
          <div className="rounded-3xl bg-forest-900 p-8 text-white">
            <p className="text-sm font-semibold uppercase tracking-widest text-forest-300">Our approach</p>
            <ul className="mt-6 space-y-5 text-sm leading-6 text-white/75">
              <li className="flex gap-3"><span className="text-forest-300">01</span><span>Ask for only what is needed to complete the requested operation.</span></li>
              <li className="flex gap-3"><span className="text-forest-300">02</span><span>Use plain language about how server-side processing works.</span></li>
              <li className="flex gap-3"><span className="text-forest-300">03</span><span>Keep the experience focused, accessible, and free of unnecessary friction.</span></li>
            </ul>
          </div>
        </div>
        <div className="mx-auto mt-16 max-w-4xl border-t border-black/10 pt-10 text-center">
          <h2 className="text-2xl font-semibold text-ink">Ready to clean up an image?</h2>
          <Link to="/#tools" className="button-primary mt-6">Start converting</Link>
        </div>
      </section>
    </>
  )
}
