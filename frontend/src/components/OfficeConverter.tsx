import { useState, type ChangeEvent } from 'react'
import { convertOffice } from '../services/api'
import type { ProcessedFile } from '../types/conversion'
import { downloadBlob } from '../utils/fileDownload'
import { ProcessingModeBadge, ProcessingModeInfo } from './ProcessingMode'

const matrix: Record<string, string[]> = {
  xlsx: ['csv', 'ods', 'pdf'], xls: ['csv', 'xlsx', 'pdf'], ods: ['csv', 'xlsx', 'pdf'], csv: ['xlsx', 'ods'],
  pptx: ['pdf', 'odp'], ppt: ['pptx', 'pdf'], odp: ['pptx', 'pdf'],
}

export function OfficeConverter() {
  const [file, setFile] = useState<File>()
  const [output, setOutput] = useState('')
  const [result, setResult] = useState<ProcessedFile>()
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(false)
  const extension = file?.name.split('.').pop()?.toLowerCase() || ''
  const options = matrix[extension] || []
  const choose = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    setFile(selected); setResult(undefined); setError(undefined)
    const next = selected?.name.split('.').pop()?.toLowerCase() || ''
    setOutput((matrix[next] || [])[0] || '')
  }
  const run = async () => {
    if (!file || !output) return
    setLoading(true); setError(undefined)
    try { setResult(await convertOffice(file, output)) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Office conversion failed.') }
    finally { setLoading(false) }
  }
  return <section className="px-5 pb-24 sm:px-8 lg:px-10"><div className="mx-auto max-w-4xl rounded-3xl border border-black/[0.08] bg-white p-6 shadow-card sm:p-8">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-ink">Spreadsheet and presentation converter</h2><p className="mt-1 text-sm text-slate-500">XLSX, XLS, ODS, CSV, PPTX, PPT and ODP</p></div><ProcessingModeBadge mode="server" /></div>
    <ProcessingModeInfo mode="server" title="Server conversion" description="Office conversion uses an isolated, time-limited LibreOffice process. Uploaded files are treated as untrusted and macros are not deliberately executed." className="mt-5 p-4" />
    <input type="file" accept=".xlsx,.xls,.ods,.csv,.pptx,.ppt,.odp" onChange={choose} className="file-picker mt-5" />
    {options.length > 0 && <label className="mt-4 block text-sm font-semibold">Output format<select value={output} onChange={(event) => setOutput(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 p-3">{options.map((value) => <option key={value}>{value.toUpperCase()}</option>)}</select></label>}
    <button type="button" disabled={!file || !output || loading} onClick={() => void run()} className="button-primary mt-5 w-full">{loading ? 'Converting on the server…' : 'Convert file'}</button>
    {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
    {result && <div className="mt-4 rounded-xl bg-forest-50 p-4"><p className="text-sm text-forest-900">{result.filename}</p><button type="button" onClick={() => downloadBlob(result.blob, result.filename)} className="button-primary mt-3">Download</button></div>}
    <p className="mt-4 text-xs leading-5 text-slate-500">Workbook-to-CSV returns one CSV per sheet in a ZIP when needed. Styles, charts, formulas, macros, transitions and external links may change or be omitted.</p>
  </div></section>
}
