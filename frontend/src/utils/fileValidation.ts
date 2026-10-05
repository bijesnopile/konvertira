import { LocalImageProcessingError, type LocalImageFormat } from '../types/image'
import { asciiAt, formatFromFilename, formatFromHeader, formatFromMimeType } from './imageFormats'

function positiveEnvironmentNumber(value: string | undefined, fallback: number): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export const LOCAL_IMAGE_LIMITS = Object.freeze({
  maxSizeMb: positiveEnvironmentNumber(import.meta.env.VITE_LOCAL_IMAGE_MAX_SIZE_MB, 50),
  maxPixels: positiveEnvironmentNumber(import.meta.env.VITE_LOCAL_IMAGE_MAX_PIXELS, 40_000_000),
})

export interface LocalFileDescriptor {
  name: string
  type: string
  size: number
}

export function validateLocalImageDescriptor(file: LocalFileDescriptor): void {
  if (!formatFromMimeType(file.type) && !formatFromFilename(file.name)) {
    throw new LocalImageProcessingError(
      'This format is not currently supported for local processing.',
    )
  }
  if (file.size <= 0) {
    throw new LocalImageProcessingError('This image is empty. Choose another file.')
  }
  if (file.size > LOCAL_IMAGE_LIMITS.maxSizeMb * 1024 * 1024) {
    throw new LocalImageProcessingError(
      `This image is larger than the ${LOCAL_IMAGE_LIMITS.maxSizeMb} MB local-processing safety limit.`,
    )
  }
}

export async function detectLocalImageFormat(file: File): Promise<LocalImageFormat> {
  validateLocalImageDescriptor(file)
  const header = new Uint8Array(await file.slice(0, 16).arrayBuffer())
  const detected = formatFromHeader(header)
  if (!detected) {
    throw new LocalImageProcessingError(
      'This file is corrupted or is not a supported JPG, PNG, or WEBP image.',
    )
  }
  return detected
}

export function validatePixelCount(width: number, height: number): void {
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) || width <= 0 || height <= 0) {
    throw new LocalImageProcessingError('The browser reported invalid image dimensions.')
  }
  if (width * height > LOCAL_IMAGE_LIMITS.maxPixels) {
    const megapixels = Math.round(LOCAL_IMAGE_LIMITS.maxPixels / 1_000_000)
    throw new LocalImageProcessingError(
      `This image exceeds the ${megapixels}-megapixel browser safety limit. Try a smaller image.`,
    )
  }
}

export async function rejectAnimatedWebP(file: File, format: LocalImageFormat): Promise<void> {
  if (format !== 'webp') return

  const bytes = new Uint8Array(await file.slice(0, Math.min(file.size, 64 * 1024)).arrayBuffer())
  const hasAnimationFlag = asciiAt(bytes, 12, 'VP8X') && bytes.length > 20 && (bytes[20] & 0x02) !== 0
  const hasAnimationChunk = findAscii(bytes, 'ANIM') || findAscii(bytes, 'ANMF')
  if (hasAnimationFlag || hasAnimationChunk) {
    throw new LocalImageProcessingError(
      'Animated WEBP images are not currently supported for local conversion.',
    )
  }
}

function findAscii(bytes: Uint8Array, text: string): boolean {
  for (let offset = 0; offset <= bytes.length - text.length; offset += 1) {
    if (asciiAt(bytes, offset, text)) return true
  }
  return false
}
