import { useState, type ChangeEvent } from 'react'
import { FORMAT_REGISTRY } from '../formats/registry'
import { removeImageBackground } from '../services/api'
import type { ProcessedFile } from '../types/conversion'
import { downloadBlob } from '../utils/fileDownload'
import { ProcessingModeBadge, ProcessingModeInfo } from './ProcessingMode'

const supported = FORMAT_REGISTRY.filter((format) => format.operationModes?.removeBackground?.includes('server'))

export function BackgroundRemoval() {
  const [file, setFile] = useState<File>()
  const [format, setFormat] = useState<'png' | 'webp'>('png')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProcessedFile>()
  const [error, setError] = useState<string>()
  const choose = (event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0])
    setResult(undefined)
    setError(undefined)
  }
  const process = async () => {
    if (!file || loading) return
    setLoading(true)
    setResult(undefined)
    setError(undefined)
    try { setResult(await removeImageBackground(file, format)) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Background removal failed.') }
    finally { setLoading(false) }
  }
  return <section className="px-5 pb-24 sm:px-8 lg:px-10" aria-labelledby="background-heading">
    <div className="mx-auto max-w-4xl rounded-3xl border border-black/[0.08] bg-white p-6 shadow-card sm:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 id="background-heading" className="text-lg font-semibold text-ink">Remove background</h2><ProcessingModeBadge mode="server" /></div>
      <ProcessingModeInfo mode="server" title="Upload required" description="This operation uploads the image to Konvertira for temporary server-side background removal." className="mt-5 p-4" />
      <input type="file" className="file-picker mt-5" accept={supported.flatMap((format) => format.extensions).join(',')} onChange={choose} disabled={loading} aria-label="Choose image for background removal" />
      <p className="mt-3 text-xs text-slate-500">{supported.map((format) => format.label).join(', ')} · Static images only · Up to 12 megapixels (server limit may vary)</p>
      <label className="mt-5 block text-sm font-semibold">Transparent output<select className="ml-3 rounded-xl border border-slate-300 p-3" value={format} disabled={loading} onChange={(event) => { setFormat(event.target.value as 'png' | 'webp'); setResult(undefined) }}><option value="png">PNG</option><option value="webp">WebP</option></select></label>
      <p className="mt-4 text-sm text-slate-600">Automatic segmentation may need refinement around hair, fur, shadows, glass, semi-transparent objects, or similar foreground and background colors. It does not guarantee anonymity or removal of visible sensitive information.</p>
      <button className="button-primary mt-5 w-full" type="button" disabled={!file || loading} onClick={() => void process()}>{loading ? 'Removing background on the server…' : 'Upload and remove background'}</button>
      {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
      {result && <div className="mt-5 rounded-xl bg-forest-50 p-4 text-sm"><p>A new transparent image was created.</p><button type="button" className="button-primary mt-3" onClick={() => downloadBlob(result.blob, result.filename)}>Download result</button></div>}
    </div>
  </section>
}
