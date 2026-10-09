import type { LocalImageFormat, LocalImageMimeType } from '../types/image'
import {
  formatFromFilename as registryFormatFromFilename,
  formatFromMimeType as registryFormatFromMimeType,
  formatFromId,
  formatsForMode,
} from '../formats/registry'

const LOCAL_IMAGES = formatsForMode('local', 'image')
const LOCAL_IMAGE_IDS = new Set(LOCAL_IMAGES.map((format) => format.id))

export const LOCAL_IMAGE_ACCEPT = LOCAL_IMAGES
  .flatMap((format) => [...format.extensions, format.preferredMimeType])
  .join(',')

export const LOCAL_IMAGE_FORMATS = Object.freeze(
  LOCAL_IMAGES.map((format) => format.id as LocalImageFormat),
)

function asLocalImageFormat(id: string | undefined): LocalImageFormat | undefined {
  return id && LOCAL_IMAGE_IDS.has(id) ? id as LocalImageFormat : undefined
}

export function formatFromMimeType(mimeType: string): LocalImageFormat | undefined {
  return asLocalImageFormat(registryFormatFromMimeType(mimeType)?.id)
}

export function formatFromFilename(filename: string): LocalImageFormat | undefined {
  return asLocalImageFormat(registryFormatFromFilename(filename)?.id)
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
  return formatFromId(format)?.preferredMimeType as LocalImageMimeType
}

export function extensionForFormat(format: LocalImageFormat): 'jpg' | 'png' | 'webp' {
  return formatFromId(format)?.preferredExtension.slice(1) as 'jpg' | 'png' | 'webp'
}

export function formatLabel(format: LocalImageFormat): 'JPG' | 'PNG' | 'WEBP' {
  return (format === 'jpeg' ? 'JPG' : formatFromId(format)?.label) as 'JPG' | 'PNG' | 'WEBP'
}

export function isLossyFormat(format: LocalImageFormat): boolean {
  return formatFromId(format)?.capabilities.quality ?? false
}

export function requiresOpaqueBackground(format: LocalImageFormat): boolean {
  return formatFromId(format)?.constraints.includes('no_transparency') ?? false
}

export function asciiAt(bytes: Uint8Array, offset: number, text: string): boolean {
  if (offset + text.length > bytes.length) return false
  for (let index = 0; index < text.length; index += 1) {
    if (bytes[offset + index] !== text.charCodeAt(index)) return false
  }
  return true
}
