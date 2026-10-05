import type { ReactNode } from 'react'

interface PageIntroProps {
  eyebrow: string
  title: string
  children: ReactNode
}

export function PageIntro({ eyebrow, title, children }: PageIntroProps) {
  return (
    <div className="border-b border-black/[0.06] bg-white">
      <div className="mx-auto max-w-4xl px-5 py-16 sm:px-8 sm:py-24">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-6xl">{title}</h1>
        <div className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">{children}</div>
      </div>
    </div>
  )
}
