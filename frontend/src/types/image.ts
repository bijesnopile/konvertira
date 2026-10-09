export type LocalImageFormat = 'jpeg' | 'png' | 'webp'
export type LocalImageMimeType = 'image/jpeg' | 'image/png' | 'image/webp'
export type LocalImageAction = 'remove-metadata' | 'convert-image'
export type ProcessingErrorCode =
  | 'unsupported_format'
  | 'unsupported_conversion'
  | 'invalid_file'
  | 'file_too_large'
  | 'decoded_content_too_large'
  | 'conversion_failed'
  | 'unsupported_feature'

export interface LocalImageInfo {
  filename: string
  size: number
  mimeType: string
  width: number
  height: number
  format: LocalImageFormat
}

export interface LocalImageProcessOptions {
  action: LocalImageAction
  outputFormat?: LocalImageFormat
  qualityPercent?: number
  width?: number
  height?: number
  scalePercent?: number
  preserveAspectRatio?: boolean
  allowUpscale?: boolean
  backgroundColor?: string
}

export interface LocalImageResult {
  blob: Blob
  filename: string
  mimeType: LocalImageMimeType
  format: LocalImageFormat
  size: number
  width: number
  height: number
  processingMode: 'local'
}

export class LocalImageProcessingError extends Error {
  readonly code: ProcessingErrorCode

  constructor(message: string, code: ProcessingErrorCode = 'invalid_file') {
    super(message)
    this.name = 'LocalImageProcessingError'
    this.code = code
  }
}
