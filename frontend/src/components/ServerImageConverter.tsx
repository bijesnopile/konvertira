import { useRef, useState, type ChangeEvent } from 'react'
import { convertImage } from '../services/api'
import type { OutputFormat, ProcessedFile } from '../types/conversion'
import { downloadBlob } from '../utils/fileDownload'
import { formatBytes } from '../utils/files'
import { ProcessingModeBadge, ProcessingModeInfo } from './ProcessingMode'
import { CONVERSION_REGISTRY, formatFromFilename, formatFromMimeType } from '../formats/registry'

const SERVER_INPUT_ACCEPT = '.jpg,.jpeg,.png,.webp,.heic,.heif,.avif,.gif,image/jpeg,image/png,image/webp,image/heic,image/heif,image/avif,image/gif'
const asOutputFormat = (id: string): OutputFormat => id === 'jpeg' ? 'jpg' : id as OutputFormat

export function ServerImageConverter() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File>()
  const [format, setFormat] = useState<OutputFormat>('jpg')
  const [quality, setQuality] = useState(85)
  const [width, setWidth] = useState('')
  const [height, setHeight] = useState('')
  const [targetKb, setTargetKb] = useState('')
  const [backgroundColor, setBackgroundColor] = useState('#ffffff')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>()
  const [result, setResult] = useState<ProcessedFile>()

  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    event.target.value = ''
    if (!selected) return
    setFile(selected)
    const source = formatFromFilename(selected.name) || formatFromMimeType(selected.type)
    const firstTarget = CONVERSION_REGISTRY.find((edge) => edge.source === source?.id && edge.executionModes.includes('server'))?.target
    if (firstTarget) setFormat(asOutputFormat(firstTarget))
    setResult(undefined)
    setError(undefined)
  }

  const process = async () => {
    if (!file || loading) return
    setLoading(true)
    setError(undefined)
    try {
      setResult(await convertImage(file, format, {
        quality,
        width: width ? Number(width) : undefined,
        height: height ? Number(height) : undefined,
        targetSizeBytes: targetKb && format !== 'png' ? Number(targetKb) * 1024 : undefined,
        backgroundColor,
        allowUpscale: false,
      }))
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Server processing failed.')
    } finally {
      setLoading(false)
    }
  }

  const source = file ? (formatFromFilename(file.name) || formatFromMimeType(file.type)) : undefined
  const outputs = CONVERSION_REGISTRY
    .filter((edge) => edge.source === source?.id && edge.executionModes.includes('server'))
    .map((edge) => asOutputFormat(edge.target))

  return (
    <section className="px-5 pb-24 sm:px-8 lg:px-10" aria-labelledby="server-image-heading">
      <div className="mx-auto max-w-4xl rounded-3xl border border-black/[0.08] bg-white p-6 shadow-card sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 id="server-image-heading" className="text-lg font-semibold text-ink">Advanced image converter</h2><p className="mt-1 text-sm text-slate-500">HEIC, AVIF, static GIF, target-size, and server codec workflows</p></div>
          <ProcessingModeBadge mode="server" />
        </div>
        <ProcessingModeInfo mode="server" title="Upload required" description="Selecting Process uploads this file to Konvertira for temporary server-side conversion. There is no automatic upload or fallback from the local tool." className="mt-5 p-4" />
        <input ref={inputRef} type="file" accept={SERVER_INPUT_ACCEPT} onChange={chooseFile} className="sr-only" />
        <button type="button" onClick={() => inputRef.current?.click()} className="button-file mt-5">{file ? 'Choose another file' : 'Choose a supported image'}</button>
        {file && <p className="mt-3 text-sm text-slate-600">{file.name} · {formatBytes(file.size)}</p>}
        <div className="mt-5 flex flex-wrap gap-3">
          {outputs.map((output) => <button type="button" key={output} onClick={() => setFormat(output)} className={format === output ? 'button-primary' : 'button-secondary'}>{output.toUpperCase()}</button>)}
        </div>
        {format !== 'png' && <label className="mt-5 block text-sm font-semibold text-ink">Quality: {quality}%<input type="range" min="10" max="100" step="5" value={quality} onChange={(event) => setQuality(Number(event.target.value))} className="mt-2 block w-full accent-forest-700" /></label>}
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <label className="text-sm font-semibold">Max width<input type="number" min="1" placeholder="Original" value={width} onChange={(event) => setWidth(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 p-3" /></label>
          <label className="text-sm font-semibold">Max height<input type="number" min="1" placeholder="Original" value={height} onChange={(event) => setHeight(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 p-3" /></label>
          <label className="text-sm font-semibold">Target size (KB)<input type="number" min="1" disabled={format === 'png'} placeholder="Best effort" value={targetKb} onChange={(event) => setTargetKb(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 p-3" /></label>
        </div>
        {format === 'jpg' && <label className="mt-4 block text-sm font-semibold">Transparency background<input type="color" value={backgroundColor} onChange={(event) => setBackgroundColor(event.target.value)} className="ml-3 h-9 w-14 align-middle" /></label>}
        <button type="button" className="button-primary mt-5 w-full" disabled={!file || loading} onClick={() => void process()}>{loading ? 'Processing on the server…' : 'Upload and convert'}</button>
        {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
        {result && <div className="mt-5 rounded-xl bg-forest-50 p-4 text-sm text-forest-900"><p>{result.filename} · {formatBytes(result.blob.size)}{result.width && result.height ? ` · ${result.width} × ${result.height}` : ''}</p><button type="button" onClick={() => downloadBlob(result.blob, result.filename)} className="button-primary mt-3">Download</button></div>}
        <p className="mt-4 text-xs leading-5 text-slate-500">Animated GIF, AVIF, or WebP files are rejected rather than silently flattened. Conversion re-encodes pixels without intentionally copying source metadata; color-profile details may change.</p>
      </div>
    </section>
  )
}
