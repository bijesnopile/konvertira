import { useState, type ChangeEvent } from 'react'
import { convertDocument } from '../services/api'
import type { ProcessedFile } from '../types/conversion'
import { downloadBlob } from '../utils/fileDownload'
import { ProcessingModeBadge, ProcessingModeInfo } from './ProcessingMode'

const outputs: Record<string, string[]> = {
  docx: ['txt', 'pdf', 'odt'], doc: ['docx', 'pdf'], odt: ['docx', 'pdf'],
  rtf: ['docx', 'pdf'], txt: ['docx', 'pdf'], md: ['html', 'docx', 'pdf'],
  markdown: ['html', 'docx', 'pdf'], html: ['txt'], htm: ['txt'],
}

export function DocumentConverter() {
  const [file, setFile] = useState<File>()
  const [output, setOutput] = useState('pdf')
  const [result, setResult] = useState<ProcessedFile>()
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(false)
  const extension = file?.name.split('.').pop()?.toLowerCase() || ''
  const available = outputs[extension] || []
  const choose = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0]
    setFile(selected); setResult(undefined); setError(undefined)
    const nextExtension = selected?.name.split('.').pop()?.toLowerCase() || ''
    setOutput((outputs[nextExtension] || [])[0] || '')
  }
  const run = async () => {
    if (!file || !output) return
    setLoading(true); setError(undefined)
    try { setResult(await convertDocument(file, output)) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Document conversion failed.') }
    finally { setLoading(false) }
  }
  return <section className="px-5 pb-24 sm:px-8 lg:px-10"><div className="mx-auto max-w-4xl rounded-3xl border border-black/[0.08] bg-white p-6 shadow-card sm:p-8">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold text-ink">Document converter</h2><p className="mt-1 text-sm text-slate-500">DOCX, DOC, ODT, RTF, TXT, Markdown and HTML</p></div><ProcessingModeBadge mode="server" /></div>
    <ProcessingModeInfo mode="server" title="Server conversion" description="The document is uploaded only when you start conversion. Complex layouts, fonts, macros and embedded objects may change or be omitted." className="mt-5 p-4" />
    <input type="file" accept=".docx,.doc,.odt,.rtf,.txt,.md,.markdown,.html,.htm" onChange={choose} className="mt-5 block w-full text-sm" />
    {file && available.length > 0 && <label className="mt-4 block text-sm font-semibold">Output format<select value={output} onChange={(event) => setOutput(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 p-3">{available.map((value) => <option key={value}>{value.toUpperCase()}</option>)}</select></label>}
    <button type="button" disabled={!file || !output || loading} onClick={() => void run()} className="button-primary mt-5 w-full">{loading ? 'Converting on the server…' : 'Convert document'}</button>
    {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
    {result && <div className="mt-4 rounded-xl bg-forest-50 p-4"><p className="text-sm text-forest-900">{result.filename}</p><button type="button" onClick={() => downloadBlob(result.blob, result.filename)} className="button-primary mt-3">Download</button></div>}
    <p className="mt-4 text-xs leading-5 text-slate-500">HTML scripts, styles and embeds are not executed. Conversion does not guarantee malware sanitization or perfect Office fidelity.</p>
  </div></section>
}
