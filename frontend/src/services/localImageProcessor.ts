import {
  LocalImageProcessingError,
  type LocalImageFormat,
  type LocalImageInfo,
  type LocalImageProcessOptions,
  type LocalImageResult,
} from '../types/image'
import {
  extensionForFormat,
  mimeTypeForFormat,
  requiresOpaqueBackground,
} from '../utils/imageFormats'
import { safeOutputFilename } from '../utils/files'
import {
  detectLocalImageFormat,
  rejectAnimatedWebP,
  validateLocalImageDescriptor,
  validatePixelCount,
} from '../utils/fileValidation'
import { conversionCapability } from '../formats/registry'

export const JPEG_BACKGROUND_COLOR = '#ffffff'

interface DecodedImage {
  source: CanvasImageSource
  width: number
  height: number
  release: () => void
}

export function qualityPercentToCanvas(qualityPercent = 90): number {
  return Math.min(100, Math.max(10, qualityPercent)) / 100
}

export function calculateLocalResizeDimensions(
  originalWidth: number,
  originalHeight: number,
  options: Pick<LocalImageProcessOptions, 'width' | 'height' | 'scalePercent' | 'preserveAspectRatio' | 'allowUpscale'>,
): { width: number; height: number } {
  if (options.scalePercent !== undefined && (options.width !== undefined || options.height !== undefined)) {
    throw new LocalImageProcessingError('Use either percentage resize or width/height, not both.')
  }
  let width = originalWidth
  let height = originalHeight
  if (options.scalePercent !== undefined) {
    if (options.scalePercent < 1 || options.scalePercent > 1000) {
      throw new LocalImageProcessingError('Resize percentage must be between 1 and 1000.')
    }
    width = Math.max(1, Math.round(originalWidth * options.scalePercent / 100))
    height = Math.max(1, Math.round(originalHeight * options.scalePercent / 100))
  } else if (options.width !== undefined || options.height !== undefined) {
    if ((options.width !== undefined && options.width <= 0) || (options.height !== undefined && options.height <= 0)) {
      throw new LocalImageProcessingError('Resize dimensions must be positive integers.')
    }
    if (options.preserveAspectRatio !== false) {
      const widthRatio = options.width === undefined ? Number.POSITIVE_INFINITY : options.width / originalWidth
      const heightRatio = options.height === undefined ? Number.POSITIVE_INFINITY : options.height / originalHeight
      const ratio = Math.min(widthRatio, heightRatio)
      width = Math.max(1, Math.round(originalWidth * ratio))
      height = Math.max(1, Math.round(originalHeight * ratio))
    } else {
      width = options.width ?? originalWidth
      height = options.height ?? originalHeight
    }
  }
  if (!options.allowUpscale && (width > originalWidth || height > originalHeight)) {
    width = originalWidth
    height = originalHeight
  }
  validatePixelCount(width, height)
  return { width, height }
}

export async function getImageInfo(file: File): Promise<LocalImageInfo> {
  validateLocalImageDescriptor(file)
  const format = await detectLocalImageFormat(file)
  await rejectAnimatedWebP(file, format)
  const decoded = await decodeImage(file)
  try {
    validatePixelCount(decoded.width, decoded.height)
    return {
      filename: file.name,
      size: file.size,
      mimeType: file.type || mimeTypeForFormat(format),
      width: decoded.width,
      height: decoded.height,
      format,
    }
  } finally {
    decoded.release()
  }
}

export async function processImageLocally(
  file: File,
  options: LocalImageProcessOptions,
): Promise<LocalImageResult> {
  validateLocalImageDescriptor(file)
  const inputFormat = await detectLocalImageFormat(file)
  await rejectAnimatedWebP(file, inputFormat)
  const outputFormat = options.action === 'remove-metadata'
    ? inputFormat
    : options.outputFormat
  if (!outputFormat) {
    throw new LocalImageProcessingError('Choose an output format before processing.', 'unsupported_conversion')
  }
  if (options.action === 'convert-image' && !conversionCapability(inputFormat, outputFormat, 'local')) {
    throw new LocalImageProcessingError(
      `Conversion from ${inputFormat.toUpperCase()} to ${outputFormat.toUpperCase()} is not supported locally.`,
      'unsupported_conversion',
    )
  }

  const decoded = await decodeImage(file)
  let canvas: HTMLCanvasElement | undefined
  try {
    validatePixelCount(decoded.width, decoded.height)
    const outputDimensions = calculateLocalResizeDimensions(decoded.width, decoded.height, options)
    canvas = document.createElement('canvas')
    canvas.width = outputDimensions.width
    canvas.height = outputDimensions.height
    const context = canvas.getContext('2d', { alpha: !requiresOpaqueBackground(outputFormat) })
    if (!context) {
      throw new LocalImageProcessingError('Your browser could not start the local image processor.')
    }

    if (requiresOpaqueBackground(outputFormat)) {
      context.fillStyle = options.backgroundColor || JPEG_BACKGROUND_COLOR
      context.fillRect(0, 0, canvas.width, canvas.height)
    }
    context.drawImage(decoded.source, 0, 0, outputDimensions.width, outputDimensions.height)

    const mimeType = mimeTypeForFormat(outputFormat)
    const blob = await canvasToBlob(
      canvas,
      mimeType,
      qualityPercentToCanvas(options.qualityPercent),
    )
    if (blob.type && blob.type !== mimeType) {
      throw new LocalImageProcessingError(
        `Your browser does not support creating ${outputFormat.toUpperCase()} images.`,
        'unsupported_feature',
      )
    }

    return {
      blob,
      filename: safeOutputFilename(
        file.name,
        extensionForFormat(outputFormat),
        options.action === 'remove-metadata' ? '-clean' : '',
      ),
      mimeType,
      format: outputFormat,
      size: blob.size,
      width: outputDimensions.width,
      height: outputDimensions.height,
      processingMode: 'local',
    }
  } catch (error) {
    if (error instanceof LocalImageProcessingError) throw error
    throw new LocalImageProcessingError(
      'Local processing failed. The image may be corrupted or too large for this browser.',
    )
  } finally {
    decoded.release()
    if (canvas) {
      canvas.width = 1
      canvas.height = 1
    }
  }
}

export function convertImageLocally(
  file: File,
  outputFormat: LocalImageFormat,
  qualityPercent = 90,
): Promise<LocalImageResult> {
  return processImageLocally(file, {
    action: 'convert-image',
    outputFormat,
    qualityPercent,
  })
}

export function removeImageMetadataLocally(
  file: File,
  qualityPercent = 90,
): Promise<LocalImageResult> {
  return processImageLocally(file, { action: 'remove-metadata', qualityPercent })
}

async function decodeImage(file: File): Promise<DecodedImage> {
  if (typeof createImageBitmap === 'function') {
    try {
      const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
      return {
        source: bitmap,
        width: bitmap.width,
        height: bitmap.height,
        release: () => bitmap.close(),
      }
    } catch {
      // Older browsers may not support the orientation option; the image fallback does.
    }
  }
  return decodeWithImageElement(file)
}

async function decodeWithImageElement(file: File): Promise<DecodedImage> {
  const objectUrl = URL.createObjectURL(file)
  const image = new Image()
  image.decoding = 'async'
  image.src = objectUrl
  try {
    if (typeof image.decode === 'function') {
      await image.decode()
    } else {
      await new Promise<void>((resolve, reject) => {
        image.onload = () => resolve()
        image.onerror = () => reject(new Error('Image decode failed'))
      })
    }
  } catch {
    URL.revokeObjectURL(objectUrl)
    throw new LocalImageProcessingError(
      'This image could not be decoded in your browser. It may be corrupted or unsupported.',
    )
  }

  return {
    source: image,
    width: image.naturalWidth,
    height: image.naturalHeight,
    release: () => {
      image.src = ''
      URL.revokeObjectURL(objectUrl)
    },
  }
}

function canvasToBlob(
  canvas: HTMLCanvasElement,
  mimeType: string,
  quality: number,
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new LocalImageProcessingError('Your browser could not create the processed image.'))
        return
      }
      resolve(blob)
    }, mimeType, quality)
  })
}

// Canvas re-encoding intentionally carries pixel data only. It may alter color profiles
// and encoding details, and it does not guarantee removal of every conceivable privacy artifact.
