import { useState, type ChangeEvent } from 'react'
import { inspectFileMetadata, removeFileMetadata } from '../services/api'
import type { ProcessedFile } from '../types/conversion'
import { downloadBlob } from '../utils/fileDownload'
import { ProcessingModeBadge, ProcessingModeInfo } from './ProcessingMode'
import { formatFromFilename, formatFromMimeType } from '../formats/registry'

interface Field { category: string; key: string; label: string; value: string; source: string; sensitive: boolean; removable: boolean }

export function MetadataPrivacyTool() {
  const [file, setFile] = useState<File>()
  const [fields, setFields] = useState<Field[]>([])
  const [warning, setWarning] = useState('')
  const [result, setResult] = useState<ProcessedFile>()
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(false)
  const format = file ? (formatFromFilename(file.name) || formatFromMimeType(file.type)) : undefined
  const canRemove = format?.capabilities.removeMetadata === true
  const choose = (event: ChangeEvent<HTMLInputElement>) => { setFile(event.target.files?.[0]); setFields([]); setResult(undefined); setError(undefined) }
  const inspect = async () => {
    if (!file) return; setLoading(true); setError(undefined)
    try { const data = await inspectFileMetadata(file); setFields((data.fields as Field[]) || []); setWarning(String(data.warning || '')) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Metadata inspection failed.') }
    finally { setLoading(false) }
  }
  const remove = async () => {
    if (!file) return; setLoading(true); setError(undefined)
    try { setResult(await removeFileMetadata(file)) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Metadata removal failed.') }
    finally { setLoading(false) }
  }
  return <section className="px-5 pb-24 sm:px-8 lg:px-10"><div className="mx-auto max-w-4xl rounded-3xl border border-black/[0.08] bg-white p-6 shadow-card sm:p-8">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-ink">Metadata inspector and privacy tools</h2><p className="mt-1 text-sm text-slate-500">See common location, identity, timestamp and software fields</p></div><ProcessingModeBadge mode="server" /></div>
    <ProcessingModeInfo mode="server" title="Server inspection for mixed file formats" description="This unified inspector uploads the selected file only after you choose an action. The image cleaner on the Convert page remains a separate local workflow." className="mt-5 p-4" />
    <input type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif,.avif,.pdf,.docx,.odt,.xlsx,.ods,.pptx,.odp" onChange={choose} className="file-picker mt-5" />
    <div className="mt-5 grid gap-3 sm:grid-cols-2"><button type="button" disabled={!file || loading} onClick={() => void inspect()} className="button-secondary">Inspect metadata</button><button type="button" disabled={!file || loading || !canRemove} onClick={() => void remove()} className="button-primary">Remove supported metadata</button></div>
    {file && !canRemove && <p className="mt-3 text-xs text-slate-500">Inspection is available, but metadata removal is not implemented for this format.</p>}
    {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
    {fields.length > 0 && <div className="mt-5 max-h-96 space-y-2 overflow-auto rounded-xl bg-slate-50 p-4">{fields.map((field, index) => <dl key={`${field.key}-${index}`} className="min-w-0 border-b border-slate-200 pb-2 text-sm"><dt className="font-semibold text-ink">{field.label} {field.sensitive && <span className="text-amber-700">· potentially sensitive</span>}</dt><dd className="break-all whitespace-pre-wrap text-slate-600">{field.value}</dd><dd className="text-xs text-slate-400">{field.category} · {field.source}</dd></dl>)}</div>}
    {warning && <p className="mt-4 text-xs leading-5 text-slate-500">{warning}</p>}
    {result && <div className="mt-4 rounded-xl bg-forest-50 p-4"><p className="text-sm font-semibold text-forest-900">Supported metadata removed from a new copy</p><button type="button" onClick={() => downloadBlob(result.blob, result.filename)} className="button-primary mt-3">Download copy</button></div>}
    <p className="mt-4 text-xs leading-5 text-slate-500">Konvertira does not claim anonymous output. Removal does not redact visible content, hidden text, comments, malware, or every possible embedded identifier.</p>
  </div></section>
}
