import registryData from '../../../format_registry.json'

export type ExecutionMode = 'local' | 'server'
export type FormatCategory = 'image' | 'pdf' | 'document' | 'spreadsheet' | 'presentation' | 'text'
export type Lossiness = 'lossless' | 'typically_lossy' | 'context_dependent'

export interface FormatCapabilities {
  inspectMetadata: boolean
  removeMetadata: boolean
  merge: boolean
  split: boolean
  quality: boolean
  compression: boolean
  resize: boolean
  multiFile: boolean
}

export interface FormatDefinition {
  id: string
  label: string
  category: FormatCategory
  extensions: readonly string[]
  mimeTypes: readonly string[]
  preferredExtension: string
  preferredMimeType: string
  processorNames: readonly string[]
  implemented: boolean
  executionModes: readonly ExecutionMode[]
  operationModes?: Readonly<Partial<Record<string, readonly ExecutionMode[]>>>
  capabilities: FormatCapabilities
  lossiness: Lossiness
  constraints: readonly string[]
}

export interface ConversionCapability {
  source: string
  target: string
  executionModes: readonly ExecutionMode[]
  lossiness: Lossiness
  constraints?: readonly string[]
}

interface RegistryData {
  schemaVersion: number
  formats: FormatDefinition[]
  conversions: ConversionCapability[]
}

const registry = registryData as RegistryData
if (registry.schemaVersion !== 1) throw new Error('Unsupported format registry schema version')

const formatsById = new Map(registry.formats.map((format) => [format.id, format]))
const formatsByExtension = new Map(
  registry.formats.flatMap((format) => format.extensions.map((extension) => [extension, format] as const)),
)
const formatsByMime = new Map(
  registry.formats.flatMap((format) => format.mimeTypes.map((mime) => [mime, format] as const)),
)
const conversions = new Map(
  registry.conversions.map((conversion) => [`${conversion.source}:${conversion.target}`, conversion]),
)

export const FORMAT_REGISTRY = Object.freeze(registry.formats)
export const CONVERSION_REGISTRY = Object.freeze(registry.conversions)

export function formatFromId(value: string): FormatDefinition | undefined {
  return formatsById.get(value.trim().toLowerCase())
}

export function formatFromExtension(value: string): FormatDefinition | undefined {
  const normalized = value.trim().toLowerCase().replace(/^([^\.])/, '.$1')
  return formatsByExtension.get(normalized)
}

export function formatFromFilename(filename: string): FormatDefinition | undefined {
  const basename = filename.trim().replaceAll('\\', '/').split('/').pop() || ''
  const dot = basename.lastIndexOf('.')
  return dot >= 0 ? formatFromExtension(basename.slice(dot)) : undefined
}

export function formatFromMimeType(mimeType: string): FormatDefinition | undefined {
  return formatsByMime.get(mimeType.split(';', 1)[0].trim().toLowerCase())
}

export function normalizeFormat(value: string): FormatDefinition | undefined {
  return formatFromId(value) || formatFromExtension(value) || formatFromMimeType(value)
}

export function conversionCapability(
  source: string,
  target: string,
  mode?: ExecutionMode,
): ConversionCapability | undefined {
  const sourceFormat = normalizeFormat(source)
  const targetFormat = normalizeFormat(target)
  if (!sourceFormat || !targetFormat) return undefined
  const capability = conversions.get(`${sourceFormat.id}:${targetFormat.id}`)
  if (!capability || (mode && !capability.executionModes.includes(mode))) return undefined
  return capability
}

export function formatsForMode(
  mode: ExecutionMode,
  category?: FormatCategory,
): readonly FormatDefinition[] {
  return FORMAT_REGISTRY.filter((format) => (
    format.implemented
    && format.executionModes.includes(mode)
    && (!category || format.category === category)
  ))
}
