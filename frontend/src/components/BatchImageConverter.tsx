import { useState, type ChangeEvent } from 'react'
import { processImageLocally } from '../services/localImageProcessor'
import type { LocalImageFormat, LocalImageResult } from '../types/image'
import { downloadBlob } from '../utils/fileDownload'
import { LOCAL_IMAGE_FORMATS, formatLabel } from '../utils/imageFormats'
import { ProcessingModeBadge } from './ProcessingMode'

const MAX_BATCH_FILES = 10
type Item = { file: File; status: 'ready' | 'processing' | 'complete' | 'failed'; result?: LocalImageResult; error?: string }

export async function runLocalImageBatch(
  files: readonly File[],
  format: LocalImageFormat,
  onUpdate: (index: number, update: Pick<Item, 'status' | 'result' | 'error'>) => void,
  processor = processImageLocally,
): Promise<void> {
  for (let index = 0; index < files.length; index += 1) {
    onUpdate(index, { status: 'processing' })
    try {
      const result = await processor(files[index], { action: 'convert-image', outputFormat: format, qualityPercent: 90 })
      onUpdate(index, { status: 'complete', result })
    } catch (caught) {
      onUpdate(index, { status: 'failed', error: caught instanceof Error ? caught.message : 'Conversion failed.' })
    }
  }
}

export function BatchImageConverter() {
  const [items, setItems] = useState<Item[]>([])
  const [format, setFormat] = useState<LocalImageFormat>('jpeg')
  const [running, setRunning] = useState(false)
  const choose = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []).slice(0, MAX_BATCH_FILES)
    setItems(files.map((file) => ({ file, status: 'ready' })))
    event.target.value = ''
  }
  const run = async () => {
    if (running) return
    setRunning(true)
    await runLocalImageBatch(items.map((item) => item.file), format, (index, update) => {
      setItems((current) => current.map((item, position) => position === index ? { ...item, ...update } : item))
    })
    setRunning(false)
  }
  return <section className="rounded-3xl border border-black/[0.08] bg-white p-6 shadow-card sm:p-8">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-ink">Batch image conversion</h2><p className="mt-1 text-sm text-slate-500">Up to {MAX_BATCH_FILES} files, processed sequentially</p></div><ProcessingModeBadge mode="local" /></div>
    <input type="file" multiple accept=".jpg,.jpeg,.png,.webp" onChange={choose} className="mt-5 block w-full text-sm" aria-label="Choose images for batch conversion" />
    <fieldset className="mt-4"><legend className="text-sm font-semibold">Output format</legend><div className="mt-2 flex gap-2">{LOCAL_IMAGE_FORMATS.map((value) => <button type="button" key={value} onClick={() => setFormat(value)} className={format === value ? 'button-primary' : 'button-secondary'}>{formatLabel(value)}</button>)}</div></fieldset>
    <button type="button" disabled={!items.length || running} onClick={() => void run()} className="button-primary mt-5 w-full">{running ? 'Processing locally…' : 'Convert batch locally'}</button>
    <ul className="mt-4 space-y-2" aria-live="polite">{items.map((item, index) => <li key={`${item.file.name}-${index}`} className="flex min-w-0 items-center justify-between gap-3 rounded-lg bg-slate-50 p-3 text-sm"><span className="min-w-0 truncate">{item.file.name} · {item.status}</span>{item.result && <button type="button" onClick={() => downloadBlob(item.result!.blob, item.result!.filename)} className="button-secondary shrink-0">Download</button>}{item.error && <span className="text-red-700">{item.error}</span>}</li>)}</ul>
    <p className="mt-4 text-xs text-slate-500">Files are decoded one at a time to bound browser memory. A failed item does not stop the remaining files, and no server request is made.</p>
  </section>
}
