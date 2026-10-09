import { normalizeFormat } from '../formats/registry'

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}

export function readableImageType(file: File): string {
  const subtype = file.type.split('/')[1]
  if (subtype) return subtype === 'jpeg' ? 'JPG' : subtype.toUpperCase()
  return file.name.split('.').pop()?.toUpperCase() || 'Unknown'
}

export function safeOutputFilename(
  originalFilename: string,
  extension: string,
  suffix = '',
): string {
  const outputFormat = normalizeFormat(extension)
  if (!outputFormat?.implemented) throw new Error(`Unsupported output extension: ${extension}`)
  const basename = originalFilename.trim().replaceAll('\\', '/').split('/').pop() || 'image'
  const stem = basename.includes('.') ? basename.slice(0, basename.lastIndexOf('.')) : basename
  const safeStem = stem.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_').replace(/[. ]+$/g, '') || 'image'
  return `${safeStem}${suffix}${outputFormat.preferredExtension}`
}

export function formatSizeDifference(outputSize: number, inputSize: number): string {
  const difference = outputSize - inputSize
  if (difference === 0 || inputSize <= 0) return 'Same size'
  const percentage = Math.abs((difference / inputSize) * 100).toFixed(1)
  return `${formatBytes(Math.abs(difference))} ${difference < 0 ? 'smaller' : 'larger'} (${percentage}%)`
}
