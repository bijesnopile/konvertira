import { useState, type ChangeEvent } from 'react'
import { inspectPdfMetadata, processPdf } from '../services/api'
import type { ProcessedFile } from '../types/conversion'
import { downloadBlob } from '../utils/fileDownload'
import { ProcessingModeBadge, ProcessingModeInfo } from './ProcessingMode'

type PdfOperation = 'merge' | 'extract' | 'split' | 'reorder' | 'delete-pages' | 'to-images' | 'images-to-pdf' | 'inspect-metadata' | 'remove-metadata' | 'optimize'
const operations: { id: PdfOperation; label: string; multi?: boolean; pages?: boolean }[] = [
  { id: 'merge', label: 'Merge PDFs', multi: true },
  { id: 'extract', label: 'Extract pages', pages: true },
  { id: 'split', label: 'Split every page' },
  { id: 'reorder', label: 'Reorder pages', pages: true },
  { id: 'delete-pages', label: 'Delete pages', pages: true },
  { id: 'to-images', label: 'PDF to images', pages: true },
  { id: 'images-to-pdf', label: 'Images to PDF', multi: true },
  { id: 'inspect-metadata', label: 'Inspect metadata' },
  { id: 'remove-metadata', label: 'Remove metadata' },
  { id: 'optimize', label: 'Lossless optimize' },
]

export function PdfToolkit() {
  const [operation, setOperation] = useState<PdfOperation>('merge')
  const [files, setFiles] = useState<File[]>([])
  const [pages, setPages] = useState('1')
  const [result, setResult] = useState<ProcessedFile>()
  const [metadata, setMetadata] = useState<Record<string, unknown>>()
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(false)
  const selected = operations.find((item) => item.id === operation) ?? operations[0]

  const selectFiles = (event: ChangeEvent<HTMLInputElement>) => {
    setFiles(Array.from(event.target.files || []))
    setResult(undefined); setMetadata(undefined); setError(undefined)
  }
  const run = async () => {
    if (!files.length) return
    setLoading(true); setError(undefined); setResult(undefined); setMetadata(undefined)
    try {
      if (operation === 'inspect-metadata') {
        setMetadata(await inspectPdfMetadata(files[0]))
      } else {
        const path = `/pdf/${operation}`
        const fields: Record<string, string> = {}
        if (selected.pages && pages) fields[operation === 'reorder' ? 'order' : 'pages'] = pages
        if (operation === 'to-images') { fields.format = 'png'; fields.dpi = '144' }
        setResult(await processPdf(path, files, fields))
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'PDF processing failed.')
    } finally { setLoading(false) }
  }

  return <section id="pdf-tools" className="px-5 pb-24 sm:px-8 lg:px-10"><div className="mx-auto max-w-4xl rounded-3xl border border-black/[0.08] bg-white p-6 shadow-card sm:p-8">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-ink">PDF toolkit</h2><p className="mt-1 text-sm text-slate-500">Merge, split, reorder, convert and inspect PDFs</p></div><ProcessingModeBadge mode="server" /></div>
    <ProcessingModeInfo mode="server" title="Temporary server processing" description="PDF operations upload the selected files only after you press Process. Encrypted PDFs are rejected." className="mt-5 p-4" />
    <label className="mt-5 block text-sm font-semibold">Operation<select value={operation} onChange={(event) => { setOperation(event.target.value as PdfOperation); setFiles([]); setResult(undefined); setMetadata(undefined) }} className="mt-2 w-full rounded-lg border border-slate-300 p-3">{operations.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
    <input className="mt-4 block w-full text-sm" type="file" accept={operation === 'images-to-pdf' ? 'image/jpeg,image/png,image/webp,image/heic,image/avif' : 'application/pdf,.pdf'} multiple={selected.multi} onChange={selectFiles} />
    {selected.pages && <label className="mt-4 block text-sm font-semibold">{operation === 'reorder' ? 'Page order (example: 3,1,2)' : 'Pages (example: 1-3,5)'}<input value={pages} onChange={(event) => setPages(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 p-3" /></label>}
    <button type="button" disabled={!files.length || loading} onClick={() => void run()} className="button-primary mt-5 w-full">{loading ? 'Processing on the server…' : 'Process PDF'}</button>
    {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
    {result && <div className="mt-4 rounded-xl bg-forest-50 p-4"><p className="text-sm text-forest-900">{result.filename}</p><button type="button" onClick={() => downloadBlob(result.blob, result.filename)} className="button-primary mt-3">Download</button></div>}
    {metadata && <dl className="mt-4 grid gap-2 rounded-xl bg-slate-50 p-4 text-sm">{Object.entries(metadata).map(([key, value]) => <div key={key}><dt className="font-semibold">{key.replaceAll('_', ' ')}</dt><dd className="break-words text-slate-600">{String(value ?? '—')}</dd></div>)}</dl>}
    <p className="mt-4 text-xs leading-5 text-slate-500">Metadata removal is not redaction, malware sanitization, or proof of anonymity. Lossless optimization performs structural cleanup and does not downsample images.</p>
  </div></section>
}
