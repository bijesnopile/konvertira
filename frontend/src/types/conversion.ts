export type OutputFormat = 'jpg' | 'png' | 'webp' | 'avif'
export type ProcessingAction = 'remove-metadata' | 'convert-image'

export interface ProcessedFile {
  blob: Blob
  filename: string
  width?: number
  height?: number
  encodingAttempts?: number
}

export interface ServerImageConversionOptions {
  quality?: number
  width?: number
  height?: number
  preserveAspectRatio?: boolean
  allowUpscale?: boolean
  lossless?: boolean
  targetSizeBytes?: number
  backgroundColor?: string
}

export interface SelectedFileInfo {
  name: string
  size: number
  type: string
}

export interface MetadataInspection {
  format: string
  width: number
  height: number
  mode: string
  metadata: Record<string, string>
}
