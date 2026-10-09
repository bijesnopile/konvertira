import type { MetadataInspection, OutputFormat, ProcessedFile, ServerImageConversionOptions } from '../types/conversion'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export class ApiError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function filenameFromDisposition(disposition: string | null, fallback: string): string {
  if (!disposition) return fallback

  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch {
      return fallback
    }
  }

  const basicMatch = disposition.match(/filename="?([^";]+)"?/i)
  return basicMatch?.[1]?.trim() || fallback
}

async function getErrorMessage(response: Response): Promise<string> {
  const fallback = `The server could not process this file (error ${response.status}).`
  const contentType = response.headers.get('content-type') || ''

  try {
    if (contentType.includes('application/json')) {
      const body = (await response.json()) as { message?: string; detail?: string }
      return body.message || body.detail || fallback
    }
    const text = await response.text()
    return text.trim() || fallback
  } catch {
    return fallback
  }
}

async function postFile(
  path: string,
  file: File,
  fallbackFilename: string,
  extraFields?: Record<string, string>,
): Promise<ProcessedFile> {
  if (!API_BASE_URL) {
    throw new ApiError('The processing service is not configured. Set VITE_API_BASE_URL and rebuild the app.')
  }

  const formData = new FormData()
  formData.append('file', file)
  Object.entries(extraFields || {}).forEach(([key, value]) => formData.append(key, value))

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      body: formData,
      headers: { Accept: 'application/octet-stream' },
    })
  } catch {
    throw new ApiError('We could not reach the processing service. Check your connection and try again.')
  }

  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status)
  }

  const blob = await response.blob()
  if (blob.size === 0) {
    throw new ApiError('The processing service returned an empty file. Please try again.')
  }

  return {
    blob,
    filename: filenameFromDisposition(response.headers.get('content-disposition'), fallbackFilename),
    width: Number(response.headers.get('x-konvertira-width')) || undefined,
    height: Number(response.headers.get('x-konvertira-height')) || undefined,
    encodingAttempts: Number(response.headers.get('x-konvertira-encoding-attempts')) || undefined,
  }
}

/** POST /images/remove-metadata as multipart/form-data with a `file` field. */
export function removeMetadata(file: File): Promise<ProcessedFile> {
  const dot = file.name.lastIndexOf('.')
  const basename = dot > 0 ? file.name.slice(0, dot) : file.name
  const extension = dot > 0 ? file.name.slice(dot) : ''
  return postFile('/images/remove-metadata', file, `${basename}-clean${extension}`)
}

/** POST /images/convert with `file` and `format` multipart fields. */
export function convertImage(
  file: File,
  format: OutputFormat,
  options: ServerImageConversionOptions = {},
): Promise<ProcessedFile> {
  const dot = file.name.lastIndexOf('.')
  const basename = dot > 0 ? file.name.slice(0, dot) : file.name
  const fields: Record<string, string> = { format }
  if (options.quality !== undefined) fields.quality = String(options.quality)
  if (options.width !== undefined) fields.width = String(options.width)
  if (options.height !== undefined) fields.height = String(options.height)
  if (options.preserveAspectRatio !== undefined) fields.preserve_aspect_ratio = String(options.preserveAspectRatio)
  if (options.allowUpscale !== undefined) fields.allow_upscale = String(options.allowUpscale)
  if (options.lossless !== undefined) fields.lossless = String(options.lossless)
  if (options.targetSizeBytes !== undefined) fields.target_size_bytes = String(options.targetSizeBytes)
  if (options.backgroundColor !== undefined) fields.background_color = options.backgroundColor
  return postFile('/images/convert', file, `${basename}.${format}`, fields)
}

/** Inspect image metadata through the explicit server-backed endpoint. */
export async function inspectMetadata(file: File): Promise<MetadataInspection> {
  if (!API_BASE_URL) {
    throw new ApiError('The processing service is not configured. Set VITE_API_BASE_URL and rebuild the app.')
  }
  const formData = new FormData()
  formData.append('file', file)
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/images/inspect-metadata`, {
      method: 'POST',
      body: formData,
      headers: { Accept: 'application/json' },
    })
  } catch {
    throw new ApiError('We could not reach the processing service. Check your connection and try again.')
  }
  if (!response.ok) throw new ApiError(await getErrorMessage(response), response.status)
  return response.json() as Promise<MetadataInspection>
}

export async function processPdf(
  path: string,
  files: readonly File[],
  fields: Record<string, string> = {},
): Promise<ProcessedFile> {
  if (!API_BASE_URL) throw new ApiError('The processing service is not configured.')
  const formData = new FormData()
  const multi = path === '/pdf/merge' || path === '/pdf/images-to-pdf'
  files.forEach((file) => formData.append(multi ? 'files' : 'file', file))
  Object.entries(fields).forEach(([key, value]) => formData.append(key, value))
  const response = await fetch(`${API_BASE_URL}${path}`, { method: 'POST', body: formData })
  if (!response.ok) throw new ApiError(await getErrorMessage(response), response.status)
  const blob = await response.blob()
  return {
    blob,
    filename: filenameFromDisposition(response.headers.get('content-disposition'), 'konvertira-result'),
  }
}

export async function inspectPdfMetadata(file: File): Promise<Record<string, unknown>> {
  if (!API_BASE_URL) throw new ApiError('The processing service is not configured.')
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE_URL}/pdf/inspect-metadata`, { method: 'POST', body: formData })
  if (!response.ok) throw new ApiError(await getErrorMessage(response), response.status)
  return response.json() as Promise<Record<string, unknown>>
}

export function convertDocument(file: File, outputFormat: string): Promise<ProcessedFile> {
  const basename = file.name.includes('.') ? file.name.slice(0, file.name.lastIndexOf('.')) : file.name
  return postFile('/documents/convert', file, `${basename}.${outputFormat}`, { output_format: outputFormat })
}

export function convertOffice(file: File, outputFormat: string, delimiter?: string): Promise<ProcessedFile> {
  const basename = file.name.includes('.') ? file.name.slice(0, file.name.lastIndexOf('.')) : file.name
  const fields: Record<string, string> = { output_format: outputFormat }
  if (delimiter) fields.delimiter = delimiter
  return postFile('/office/convert', file, `${basename}.${outputFormat}`, fields)
}

export async function inspectFileMetadata(file: File): Promise<Record<string, unknown>> {
  if (!API_BASE_URL) throw new ApiError('The processing service is not configured.')
  const formData = new FormData(); formData.append('file', file)
  const response = await fetch(`${API_BASE_URL}/metadata/inspect`, { method: 'POST', body: formData })
  if (!response.ok) throw new ApiError(await getErrorMessage(response), response.status)
  return response.json() as Promise<Record<string, unknown>>
}

export function removeFileMetadata(file: File): Promise<ProcessedFile> {
  return postFile('/metadata/remove', file, `${file.name}-metadata-removed`)
}
