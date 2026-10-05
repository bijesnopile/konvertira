import type { LocalImageFormat, LocalImageMimeType } from '../types/image'

const MIME_TO_FORMAT: Record<LocalImageMimeType, LocalImageFormat> = {
  'image/jpeg': 'jpeg',
  'image/png': 'png',
  'image/webp': 'webp',
}

const FORMAT_TO_MIME: Record<LocalImageFormat, LocalImageMimeType> = {
  jpeg: 'image/jpeg',
  png: 'image/png',
  webp: 'image/webp',
}

const EXTENSION_TO_FORMAT: Record<string, LocalImageFormat> = {
  jpg: 'jpeg',
  jpeg: 'jpeg',
  png: 'png',
  webp: 'webp',
}

export const LOCAL_IMAGE_ACCEPT = '.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp'

export function formatFromMimeType(mimeType: string): LocalImageFormat | undefined {
  return MIME_TO_FORMAT[mimeType.toLowerCase() as LocalImageMimeType]
}

export function formatFromFilename(filename: string): LocalImageFormat | undefined {
  const extension = filename.trim().toLowerCase().split('.').pop() || ''
  return EXTENSION_TO_FORMAT[extension]
}

export function formatFromHeader(bytes: Uint8Array): LocalImageFormat | undefined {
  if (bytes.length >= 3 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) {
    return 'jpeg'
  }
  if (
    bytes.length >= 8
    && bytes[0] === 0x89
    && bytes[1] === 0x50
    && bytes[2] === 0x4e
    && bytes[3] === 0x47
    && bytes[4] === 0x0d
    && bytes[5] === 0x0a
    && bytes[6] === 0x1a
    && bytes[7] === 0x0a
  ) {
    return 'png'
  }
  if (
    bytes.length >= 12
    && asciiAt(bytes, 0, 'RIFF')
    && asciiAt(bytes, 8, 'WEBP')
  ) {
    return 'webp'
  }
  return undefined
}

export function mimeTypeForFormat(format: LocalImageFormat): LocalImageMimeType {
  return FORMAT_TO_MIME[format]
}

export function extensionForFormat(format: LocalImageFormat): 'jpg' | 'png' | 'webp' {
  return format === 'jpeg' ? 'jpg' : format
}

export function formatLabel(format: LocalImageFormat): 'JPG' | 'PNG' | 'WEBP' {
  return format === 'jpeg' ? 'JPG' : format.toUpperCase() as 'PNG' | 'WEBP'
}

export function isLossyFormat(format: LocalImageFormat): boolean {
  return format === 'jpeg' || format === 'webp'
}

export function requiresOpaqueBackground(format: LocalImageFormat): boolean {
  return format === 'jpeg'
}

export function asciiAt(bytes: Uint8Array, offset: number, text: string): boolean {
  if (offset + text.length > bytes.length) return false
  for (let index = 0; index < text.length; index += 1) {
    if (bytes[offset + index] !== text.charCodeAt(index)) return false
  }
  return true
}
