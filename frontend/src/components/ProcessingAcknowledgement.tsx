import { useId } from 'react'
import { ACKNOWLEDGEMENT_ERROR } from '../hooks/useProcessingAcknowledgement'

type Props = {
  accepted: boolean
  setAccepted: (value: boolean) => void
  error: boolean
  disabled?: boolean
}

export function ProcessingAcknowledgement({ accepted, setAccepted, error, disabled }: Props) {
  const id = useId()
  return <div className="processing-acknowledgement mt-5 rounded-xl border border-slate-300 bg-slate-50 p-4 text-sm leading-6 text-ink">
    <div className="flex items-start gap-3">
      <input id={id} type="checkbox" checked={accepted} disabled={disabled}
        onChange={(event) => setAccepted(event.target.checked)}
        aria-invalid={error || undefined} aria-describedby={error ? `${id}-error` : undefined}
        className="mt-1 h-5 w-5 shrink-0 cursor-pointer accent-forest-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest-700" />
      <label htmlFor={id} className="min-w-0">
        I confirm that I have the right to process this file, understand that it will be uploaded to Konvertira's server for the selected operation, and agree to the <a href="/terms" target="_blank" rel="noopener" className="underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-forest-700">Terms of Service</a>. I have read the <a href="/privacy" target="_blank" rel="noopener" className="underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-forest-700">Privacy Policy</a>.
        <span className="sr-only"> Legal links open in a new tab.</span>
      </label>
    </div>
    {error && <p id={`${id}-error`} role="alert" className="mt-2 text-red-700">{ACKNOWLEDGEMENT_ERROR}</p>}
  </div>
}
