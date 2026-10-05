export type LocalImageFormat = 'jpeg' | 'png' | 'webp'
export type LocalImageMimeType = 'image/jpeg' | 'image/png' | 'image/webp'
export type LocalImageAction = 'remove-metadata' | 'convert-image'

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
  constructor(message: string) {
    super(message)
    this.name = 'LocalImageProcessingError'
  }
}
