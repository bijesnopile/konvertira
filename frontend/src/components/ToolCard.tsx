import { type ChangeEvent, type DragEvent, useRef, useState } from 'react'
import { getImageInfo, processImageLocally } from '../services/localImageProcessor'
import type {
  LocalImageAction,
  LocalImageFormat,
  LocalImageInfo,
  LocalImageResult,
} from '../types/image'
import { downloadBlob } from '../utils/fileDownload'
import { LOCAL_IMAGE_LIMITS, validateLocalImageDescriptor } from '../utils/fileValidation'
import {
  formatLabel,
  isLossyFormat,
  LOCAL_IMAGE_ACCEPT,
  LOCAL_IMAGE_FORMATS,
} from '../utils/imageFormats'
import { formatBytes, formatSizeDifference } from '../utils/files'
import {
  PROCESSING_MODE_COPY,
  ProcessingModeBadge,
  ProcessingModeInfo,
} from './ProcessingMode'

export function ToolCard() {
  const inputRef = useRef<HTMLInputElement>(null)
  const selectionId = useRef(0)
  const [file, setFile] = useState<File>()
  const [fileInfo, setFileInfo] = useState<LocalImageInfo>()
  const [action, setAction] = useState<LocalImageAction>('remove-metadata')
  const [format, setFormat] = useState<LocalImageFormat>('jpeg')
  const [quality, setQuality] = useState(90)
  const [resizeEnabled, setResizeEnabled] = useState(false)
  const [resizeWidth, setResizeWidth] = useState<number>()
  const [resizeHeight, setResizeHeight] = useState<number>()
  const [backgroundColor, setBackgroundColor] = useState('#ffffff')
  const [dragging, setDragging] = useState(false)
  const [inspecting, setInspecting] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>()
  const [result, setResult] = useState<LocalImageResult>()

  const outputFormat = action === 'remove-metadata' ? fileInfo?.format : format
  const showQuality = outputFormat ? isLossyFormat(outputFormat) : false

  const selectFile = async (candidate?: File) => {
    const currentSelection = selectionId.current + 1
    selectionId.current = currentSelection
    setError(undefined)
    setResult(undefined)
    if (!candidate) return

    try {
      validateLocalImageDescriptor(candidate)
      setInspecting(true)
      const info = await getImageInfo(candidate)
      if (selectionId.current !== currentSelection) return
      setFile(candidate)
      setFileInfo(info)
    } catch (caught) {
      if (selectionId.current !== currentSelection) return
      setFile(undefined)
      setFileInfo(undefined)
      setError(userFacingError(caught))
    } finally {
      if (selectionId.current === currentSelection) setInspecting(false)
    }
  }

  const handleInput = (event: ChangeEvent<HTMLInputElement>) => {
    void selectFile(event.target.files?.[0])
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    void selectFile(event.dataTransfer.files?.[0])
  }

  const clearFile = () => {
    selectionId.current += 1
    setFile(undefined)
    setFileInfo(undefined)
    setResult(undefined)
    setError(undefined)
    setInspecting(false)
  }

  const changeAction = (nextAction: LocalImageAction) => {
    setAction(nextAction)
    setResult(undefined)
    setError(undefined)
  }

  const processFile = async () => {
    if (!file || !fileInfo || loading) return
    setLoading(true)
    setError(undefined)
    setResult(undefined)
    try {
      const processed = await processImageLocally(file, {
        action,
        outputFormat: format,
        qualityPercent: quality,
        width: resizeEnabled ? resizeWidth : undefined,
        height: resizeEnabled ? resizeHeight : undefined,
        preserveAspectRatio: true,
        allowUpscale: false,
        backgroundColor,
      })
      setResult(processed)
    } catch (caught) {
      setError(userFacingError(caught))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="tools" className="scroll-mt-28 px-5 pb-24 sm:px-8 lg:px-10" aria-labelledby="tool-heading">
      <div className="mx-auto max-w-4xl">
        <div className="overflow-hidden rounded-3xl border border-black/[0.08] bg-white shadow-card">
          <div className="flex flex-col gap-4 border-b border-black/[0.06] px-6 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-8">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-forest-100 text-forest-800" aria-hidden="true">
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v12" /><path d="m7 10 5 5 5-5" /><path d="M5 21h14" /></svg>
              </span>
              <div>
                <h2 id="tool-heading" className="text-lg font-semibold text-ink">Image privacy tool</h2>
                <p className="text-sm text-slate-500">Convert or clean a static image</p>
              </div>
            </div>
            <ProcessingModeBadge mode="local" />
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
                <input ref={inputRef} type="file" accept={LOCAL_IMAGE_ACCEPT} onChange={handleInput} className="sr-only" id="image-upload" />
                <div className="mb-5 grid h-14 w-14 place-items-center rounded-2xl bg-white text-forest-700 shadow-sm ring-1 ring-black/5" aria-hidden="true">
                  {inspecting ? <Spinner /> : <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M20 15v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4" /></svg>}
                </div>
                <p className="font-semibold text-ink">{inspecting ? 'Reading image details…' : 'Drag and drop your image here'}</p>
                {!inspecting && (
                  <>
                    <p className="mt-1 text-sm text-slate-500">or</p>
                    <button type="button" className="button-file mt-4" onClick={() => inputRef.current?.click()}>Browse files</button>
                  </>
                )}
                <p className="mt-5 text-xs leading-5 text-slate-500">JPG, JPEG, PNG or WEBP · Up to {LOCAL_IMAGE_LIMITS.maxSizeMb} MB<br />Static images only</p>
              </div>
            ) : fileInfo && (
              <div className="space-y-7">
                <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
                  <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-forest-100 text-xs font-bold text-forest-800">{formatLabel(fileInfo.format)}</span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-ink">{fileInfo.filename}</p>
                    <p className="mt-1 text-sm text-slate-500">{formatBytes(fileInfo.size)} <span aria-hidden="true">·</span> {fileInfo.mimeType || 'Unknown MIME type'}</p>
                    <p className="mt-1 text-xs text-slate-500">{fileInfo.width.toLocaleString()} × {fileInfo.height.toLocaleString()} px <span aria-hidden="true">·</span> Detected {formatLabel(fileInfo.format)}</p>
                  </div>
                  <button type="button" onClick={clearFile} className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-500" aria-label="Remove selected file">
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m6 6 12 12" /><path d="M18 6 6 18" /></svg>
                  </button>
                </div>

                <ProcessingModeInfo
                  mode="local"
                  title="Your file will be processed locally"
                  description="Supported image conversion and metadata removal run directly in this browser. Your image will not be uploaded."
                  className="p-4"
                />

                <fieldset>
                  <legend className="mb-3 text-sm font-semibold text-ink">What would you like to do?</legend>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <ActionOption selected={action === 'remove-metadata'} title="Remove metadata" description="Re-encode pixels without copying embedded data" onClick={() => changeAction('remove-metadata')} />
                    <ActionOption selected={action === 'convert-image'} title="Convert image" description="Create a JPG, PNG, or WEBP copy" onClick={() => changeAction('convert-image')} />
                  </div>
                </fieldset>

                {action === 'convert-image' && (
                  <fieldset>
                    <legend className="mb-3 text-sm font-semibold text-ink">Output format</legend>
                    <div className="flex flex-wrap gap-3">
                      {LOCAL_IMAGE_FORMATS.map((option) => (
                        <label key={option} className={`cursor-pointer rounded-xl border px-5 py-3 text-sm font-semibold transition-colors focus-within:ring-2 focus-within:ring-forest-500 focus-within:ring-offset-2 ${format === option ? 'border-forest-700 bg-forest-50 text-forest-800' : 'border-slate-200 text-slate-600 hover:border-slate-300'}`}>
                          <input type="radio" name="format" value={option} checked={format === option} onChange={() => { setFormat(option); setResult(undefined); setError(undefined) }} className="sr-only" />
                          {formatLabel(option)}
                        </label>
                      ))}
                    </div>
                    {format === 'jpeg' && <p className="mt-3 text-xs text-slate-500">Transparent areas are filled with white because JPEG does not support transparency.</p>}
                  </fieldset>
                )}

                {showQuality && (
                  <div>
                    <div className="mb-3 flex items-center justify-between">
                      <label htmlFor="image-quality" className="text-sm font-semibold text-ink">Output quality</label>
                      <output htmlFor="image-quality" className="text-sm font-semibold text-forest-800">{quality}%</output>
                    </div>
                    <input id="image-quality" type="range" min="10" max="100" step="5" value={quality} onChange={(event) => { setQuality(Number(event.target.value)); setResult(undefined) }} className="w-full accent-forest-700" />
                    <p className="mt-2 text-xs text-slate-500">Higher quality usually creates a larger file.</p>
                  </div>
                )}

                <div className="rounded-2xl border border-slate-200 p-4">
                  <label className="flex items-center gap-3 text-sm font-semibold text-ink">
                    <input type="checkbox" checked={resizeEnabled} onChange={(event) => { setResizeEnabled(event.target.checked); setResult(undefined) }} className="h-4 w-4 accent-forest-700" />
                    Resize image
                  </label>
                  {resizeEnabled && (
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <label className="text-xs text-slate-600">Maximum width
                        <input type="number" min="1" inputMode="numeric" value={resizeWidth ?? ''} onChange={(event) => setResizeWidth(event.target.value ? Number(event.target.value) : undefined)} placeholder={String(fileInfo.width)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                      </label>
                      <label className="text-xs text-slate-600">Maximum height
                        <input type="number" min="1" inputMode="numeric" value={resizeHeight ?? ''} onChange={(event) => setResizeHeight(event.target.value ? Number(event.target.value) : undefined)} placeholder={String(fileInfo.height)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                      </label>
                      <p className="text-xs text-slate-500 sm:col-span-2">Aspect ratio is preserved and images are not enlarged by default.</p>
                    </div>
                  )}
                </div>

                {outputFormat === 'jpeg' && (
                  <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700">
                    Transparency background
                    <input type="color" value={backgroundColor} onChange={(event) => { setBackgroundColor(event.target.value); setResult(undefined) }} aria-label="JPEG transparency background" />
                  </label>
                )}

                <button type="button" className="button-primary w-full py-3.5" onClick={() => void processFile()} disabled={loading}>
                  {loading ? <><Spinner /> {PROCESSING_MODE_COPY.local.processing}</> : 'Process image locally'}
                </button>
              </div>
            )}

            {error && (
              <div role="alert" className="mt-5 flex gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                <svg viewBox="0 0 24 24" className="mt-0.5 h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 8v5" /><path d="M12 17h.01" /></svg>
                <p>{error}</p>
              </div>
            )}

            {result && fileInfo && (
              <div className="mt-5 rounded-2xl border border-forest-200 bg-forest-50 p-5" aria-live="polite">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-700 text-white" aria-hidden="true">
                      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 12 4 4 8-8" /></svg>
                    </span>
                    <div className="min-w-0"><p className="font-semibold text-forest-900">{PROCESSING_MODE_COPY.local.successTitle}</p><p className="truncate text-sm text-forest-700">{result.filename}</p></div>
                  </div>
                  <button type="button" onClick={() => downloadBlob(result.blob, result.filename)} className="button-primary shrink-0">Download file</button>
                </div>
                <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-forest-200 pt-5 text-sm sm:grid-cols-5">
                  <ResultDetail label="Output" value={formatLabel(result.format)} />
                  <ResultDetail label="Size" value={formatBytes(result.size)} />
                  <ResultDetail label="Difference" value={formatSizeDifference(result.size, fileInfo.size)} />
                  <ResultDetail label="Dimensions" value={`${result.width.toLocaleString()} × ${result.height.toLocaleString()}`} />
                  <ResultDetail label="Mode" value="Local / Browser" />
                </dl>
                <p className="mt-5 text-sm font-medium text-forest-900">{PROCESSING_MODE_COPY.local.successDescription}</p>
                {action === 'remove-metadata' && <p className="mt-1 text-xs leading-5 text-forest-700">Re-encoded locally to remove embedded image metadata.</p>}
              </div>
            )}
          </div>
        </div>
        <div className="mt-4 text-center text-xs leading-5 text-slate-500">
          <p>Your image stays on your device for this tool. Animated images are not supported.</p>
          <p>Browser re-encoding may change compression and color-profile details.</p>
        </div>
      </div>
    </section>
  )
}

function userFacingError(error: unknown): string {
  const reason = error instanceof Error
    ? error.message
    : 'Local processing failed. Choose another image and try again.'
  return `${reason} Your image was not uploaded.`
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

function ResultDetail({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-xs text-forest-700">{label}</dt><dd className="mt-1 font-semibold text-forest-900">{value}</dd></div>
}

function Spinner() {
  return <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle className="opacity-30" cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" /><path className="opacity-90" d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" /></svg>
}
