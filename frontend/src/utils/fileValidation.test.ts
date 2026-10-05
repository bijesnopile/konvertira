import { describe, expect, it } from 'vitest'
import { LocalImageProcessingError } from '../types/image'
import {
  LOCAL_IMAGE_LIMITS,
  rejectAnimatedWebP,
  validateLocalImageDescriptor,
  validatePixelCount,
} from './fileValidation'

describe('local image validation', () => {
  it('accepts supported images by MIME type or extension', () => {
    expect(() => validateLocalImageDescriptor({ name: 'photo.bin', type: 'image/jpeg', size: 100 })).not.toThrow()
    expect(() => validateLocalImageDescriptor({ name: 'photo.webp', type: '', size: 100 })).not.toThrow()
  })

  it('rejects unsupported, empty, and oversized files', () => {
    expect(() => validateLocalImageDescriptor({ name: 'vector.svg', type: 'image/svg+xml', size: 100 })).toThrow(LocalImageProcessingError)
    expect(() => validateLocalImageDescriptor({ name: 'photo.jpg', type: 'image/jpeg', size: 0 })).toThrow('empty')
    expect(() => validateLocalImageDescriptor({ name: 'photo.jpg', type: 'image/jpeg', size: (LOCAL_IMAGE_LIMITS.maxSizeMb + 1) * 1024 * 1024 })).toThrow('safety limit')
  })

  it('rejects unsafe decoded dimensions', () => {
    expect(() => validatePixelCount(1000, 1000)).not.toThrow()
    expect(() => validatePixelCount(LOCAL_IMAGE_LIMITS.maxPixels + 1, 1)).toThrow('megapixel')
    expect(() => validatePixelCount(0, 100)).toThrow('invalid')
  })

  it('rejects animated WEBP feature flags', async () => {
    const bytes = new Uint8Array(24)
    bytes.set(new TextEncoder().encode('RIFF'), 0)
    bytes.set(new TextEncoder().encode('WEBP'), 8)
    bytes.set(new TextEncoder().encode('VP8X'), 12)
    bytes[20] = 0x02
    const file = new File([bytes], 'animation.webp', { type: 'image/webp' })
    await expect(rejectAnimatedWebP(file, 'webp')).rejects.toThrow('Animated WEBP')
  })
})
