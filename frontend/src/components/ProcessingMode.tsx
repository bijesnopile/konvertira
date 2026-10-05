import type { ReactNode } from 'react'

export type ProcessingMode = 'local' | 'server'

export const PROCESSING_MODE_COPY = {
  local: {
    badge: 'Runs in your browser',
    title: 'Processed locally',
    description: 'Your file stays on your device.',
    processing: 'Processing in your browser…',
    successTitle: 'Processed locally',
    successDescription: 'Your original file was never uploaded.',
  },
  server: {
    badge: 'Server processing',
    title: 'Temporary server processing',
    description: 'This operation requires a temporary upload.',
    processing: 'Processing on the server…',
    successTitle: 'Server processing complete',
    successDescription: 'The requested operation is complete.',
  },
} as const

interface ProcessingModeBadgeProps {
  mode: ProcessingMode
  label?: string
}

export function ProcessingModeBadge({ mode, label }: ProcessingModeBadgeProps) {
  const local = mode === 'local'
  return (
    <span className={`inline-flex w-fit items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ring-1 ring-inset ${local ? 'bg-forest-50 text-forest-800 ring-forest-200' : 'bg-slate-100 text-slate-700 ring-slate-200'}`}>
      <span className={`h-2 w-2 rounded-full ${local ? 'bg-forest-500' : 'bg-slate-400'}`} aria-hidden="true" />
      {label || PROCESSING_MODE_COPY[mode].badge}
    </span>
  )
}

interface ProcessingModeInfoProps {
  mode: ProcessingMode
  title?: string
  description?: string
  children?: ReactNode
  className?: string
}

export function ProcessingModeInfo({
  mode,
  title,
  description,
  children,
  className = '',
}: ProcessingModeInfoProps) {
  const copy = PROCESSING_MODE_COPY[mode]
  const local = mode === 'local'

  return (
    <article className={`rounded-2xl border p-5 ${local ? 'border-forest-200 bg-forest-50' : 'border-slate-200 bg-slate-50'} ${className}`}>
      <ProcessingModeBadge mode={mode} />
      <h3 className="mt-4 text-lg font-semibold text-ink">{title || copy.title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description || copy.description}</p>
      {children}
    </article>
  )
}
