import { BatchImageConverter } from '../components/BatchImageConverter'
import { DocumentConverter } from '../components/DocumentConverter'
import { MetadataPrivacyTool } from '../components/MetadataPrivacyTool'
import { OfficeConverter } from '../components/OfficeConverter'
import { PdfToolkit } from '../components/PdfToolkit'
import { ServerImageConverter } from '../components/ServerImageConverter'
import { ToolCard } from '../components/ToolCard'

export function ConvertPage() {
  return <div className="pb-8 pt-12"><header className="mx-auto max-w-4xl px-5 pb-10 sm:px-8"><p className="eyebrow">Convert</p><h1 className="mt-3 text-4xl font-semibold text-ink">Choose the workflow that matches your file.</h1><p className="mt-4 text-slate-600">Local and server processing are labeled before any action starts.</p></header><ToolCard /><div className="mx-auto max-w-4xl space-y-8 px-5 pb-24 sm:px-8"><BatchImageConverter /></div><ServerImageConverter /><DocumentConverter /><OfficeConverter /></div>
}

export function PdfToolsPage() {
  return <div className="pt-12"><header className="mx-auto max-w-4xl px-5 pb-10 sm:px-8"><p className="eyebrow">PDF tools</p><h1 className="mt-3 text-4xl font-semibold text-ink">Work with PDF pages and metadata.</h1></header><PdfToolkit /></div>
}

export function MetadataPage() {
  return <div className="pt-12"><header className="mx-auto max-w-4xl px-5 pb-10 sm:px-8"><p className="eyebrow">Metadata</p><h1 className="mt-3 text-4xl font-semibold text-ink">Inspect and remove supported metadata.</h1></header><MetadataPrivacyTool /></div>
}
