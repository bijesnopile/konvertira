export type OutputFormat = 'jpg' | 'png' | 'webp'
export type ProcessingAction = 'remove-metadata' | 'convert-image'

export interface ProcessedFile {
  blob: Blob
  filename: string
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
