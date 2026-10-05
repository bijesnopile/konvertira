import type { MetadataInspection, OutputFormat, ProcessedFile } from '../types/conversion'

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
export function convertImage(file: File, format: OutputFormat): Promise<ProcessedFile> {
  const dot = file.name.lastIndexOf('.')
  const basename = dot > 0 ? file.name.slice(0, dot) : file.name
  return postFile('/images/convert', file, `${basename}.${format}`, { format })
}

/** Prepared for the future metadata-inspection endpoint; not exposed as an active UI feature. */
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
