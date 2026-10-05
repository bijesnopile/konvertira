import { type ChangeEvent, type DragEvent, useRef, useState } from 'react'
import { convertImage, removeMetadata } from '../services/api'
import type { OutputFormat, ProcessedFile, ProcessingAction } from '../types/conversion'
import { useDownloadUrl } from '../hooks/useDownloadUrl'
import { formatBytes, readableImageType } from '../utils/files'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const ACCEPTED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
const MAX_FILE_SIZE = 20 * 1024 * 1024

export function ToolCard() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File>()
  const [action, setAction] = useState<ProcessingAction>('remove-metadata')
  const [format, setFormat] = useState<OutputFormat>('jpg')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>()
  const [result, setResult] = useState<ProcessedFile>()
  const downloadUrl = useDownloadUrl(result?.blob)

  const validateAndSetFile = (candidate?: File) => {
    setError(undefined)
    setResult(undefined)
    if (!candidate) return

    const extension = candidate.name.split('.').pop()?.toLowerCase() || ''
    if (!ACCEPTED_TYPES.includes(candidate.type) && !ACCEPTED_EXTENSIONS.includes(extension)) {
      setError('That file type is not supported. Choose a JPG, JPEG, PNG, or WEBP image.')
      return
    }
    if (candidate.size > MAX_FILE_SIZE) {
      setError('This file is larger than 20 MB. Choose a smaller image and try again.')
      return
    }
    setFile(candidate)
  }

  const handleInput = (event: ChangeEvent<HTMLInputElement>) => {
    validateAndSetFile(event.target.files?.[0])
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    validateAndSetFile(event.dataTransfer.files?.[0])
  }

  const clearFile = () => {
    setFile(undefined)
    setResult(undefined)
    setError(undefined)
  }

  const processFile = async () => {
    if (!file || loading) return
    setLoading(true)
    setError(undefined)
    setResult(undefined)
    try {
      const processed = action === 'remove-metadata'
        ? await removeMetadata(file)
        : await convertImage(file, format)
      setResult(processed)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Something went wrong while processing your file. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="tools" className="scroll-mt-28 px-5 pb-24 sm:px-8 lg:px-10" aria-labelledby="tool-heading">
      <div className="mx-auto max-w-4xl">
        <div className="overflow-hidden rounded-3xl border border-black/[0.08] bg-white shadow-card">
          <div className="border-b border-black/[0.06] px-6 py-5 sm:px-8">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-forest-100 text-forest-800" aria-hidden="true">
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v12" /><path d="m7 10 5 5 5-5" /><path d="M5 21h14" /></svg>
              </span>
              <div>
                <h2 id="tool-heading" className="text-lg font-semibold text-ink">Image privacy tool</h2>
                <p className="text-sm text-slate-500">Upload one image to get started</p>
              </div>
            </div>
          </div>

          <div className="p-5 sm:p-8">
            {!file ? (
              <div
                className={`relative flex min-h-64 flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors ${dragging ? 'border-forest-600 bg-forest-50' : 'border-slate-300 bg-slate-50/60 hover:border-forest-400 hover:bg-forest-50/40'}`}
                onDragEnter={(event) => { event.preventDefault(); setDragging(true) }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false) }}
                onDrop={handleDrop}
              >
                <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={handleInput} className="sr-only" id="image-upload" />
                <div className="mb-5 grid h-14 w-14 place-items-center rounded-2xl bg-white text-forest-700 shadow-sm ring-1 ring-black/5" aria-hidden="true">
                  <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M20 15v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4" /></svg>
                </div>
                <p className="font-semibold text-ink">Drag and drop your image here</p>
                <p className="mt-1 text-sm text-slate-500">or</p>
                <button type="button" className="button-secondary mt-4" onClick={() => inputRef.current?.click()}>Browse files</button>
                <p className="mt-5 text-xs text-slate-500">JPG, JPEG, PNG or WEBP · Max 20 MB</p>
              </div>
            ) : (
              <div className="space-y-7">
                <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
                  <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-forest-100 text-xs font-bold text-forest-800">{readableImageType(file)}</span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-ink">{file.name}</p>
                    <p className="mt-1 text-sm text-slate-500">{formatBytes(file.size)} <span aria-hidden="true">·</span> {file.type || readableImageType(file)}</p>
                  </div>
                  <button type="button" onClick={clearFile} className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-500" aria-label="Remove selected file">
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m6 6 12 12" /><path d="M18 6 6 18" /></svg>
                  </button>
                </div>

                <fieldset>
                  <legend className="mb-3 text-sm font-semibold text-ink">What would you like to do?</legend>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <ActionOption selected={action === 'remove-metadata'} title="Remove metadata" description="Remove EXIF and other embedded details" onClick={() => { setAction('remove-metadata'); setResult(undefined) }} />
                    <ActionOption selected={action === 'convert-image'} title="Convert image" description="Change the image file format" onClick={() => { setAction('convert-image'); setResult(undefined) }} />
                  </div>
                </fieldset>

                {action === 'convert-image' && (
                  <fieldset>
                    <legend className="mb-3 text-sm font-semibold text-ink">Output format</legend>
                    <div className="flex flex-wrap gap-3">
                      {(['jpg', 'png', 'webp'] as OutputFormat[]).map((option) => (
                        <label key={option} className={`cursor-pointer rounded-xl border px-5 py-3 text-sm font-semibold uppercase transition-colors focus-within:ring-2 focus-within:ring-forest-500 focus-within:ring-offset-2 ${format === option ? 'border-forest-700 bg-forest-50 text-forest-800' : 'border-slate-200 text-slate-600 hover:border-slate-300'}`}>
                          <input type="radio" name="format" value={option} checked={format === option} onChange={() => { setFormat(option); setResult(undefined) }} className="sr-only" />
                          {option}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                )}

                <button type="button" className="button-primary w-full py-3.5" onClick={processFile} disabled={loading}>
                  {loading ? <><Spinner /> Processing…</> : 'Process image'}
                </button>
              </div>
            )}

            {error && (
              <div role="alert" className="mt-5 flex gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                <svg viewBox="0 0 24 24" className="mt-0.5 h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 8v5" /><path d="M12 17h.01" /></svg>
                <p>{error}</p>
              </div>
            )}

            {result && downloadUrl && (
              <div className="mt-5 flex flex-col gap-4 rounded-2xl border border-forest-200 bg-forest-50 p-5 sm:flex-row sm:items-center sm:justify-between" role="status">
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-full bg-forest-700 text-white" aria-hidden="true">
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 12 4 4 8-8" /></svg>
                  </span>
                  <div><p className="font-semibold text-forest-900">Your file is ready</p><p className="text-sm text-forest-700">{result.filename}</p></div>
                </div>
                <a href={downloadUrl} download={result.filename} className="button-primary shrink-0">Download file</a>
              </div>
            )}
          </div>
        </div>
        <p className="mt-4 flex items-center justify-center gap-2 text-center text-xs text-slate-500">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>
          Files are sent to our processing service and retained only temporarily.
        </p>
      </div>
    </section>
  )
}

interface ActionOptionProps {
  selected: boolean
  title: string
  description: string
  onClick: () => void
}

function ActionOption({ selected, title, description, onClick }: ActionOptionProps) {
  return (
    <label className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-4 transition-colors focus-within:ring-2 focus-within:ring-forest-500 focus-within:ring-offset-2 ${selected ? 'border-forest-700 bg-forest-50' : 'border-slate-200 hover:border-slate-300'}`}>
      <input type="radio" name="action" checked={selected} onChange={onClick} className="mt-1 h-4 w-4 accent-forest-700" />
      <span><span className="block font-semibold text-ink">{title}</span><span className="mt-1 block text-sm leading-5 text-slate-500">{description}</span></span>
    </label>
  )
}

function Spinner() {
  return <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle className="opacity-30" cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" /><path className="opacity-90" d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" /></svg>
}
