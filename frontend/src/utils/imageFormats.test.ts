import { describe, expect, it } from 'vitest'
import {
  extensionForFormat,
  formatFromFilename,
  formatFromHeader,
  formatFromMimeType,
  mimeTypeForFormat,
  requiresOpaqueBackground,
} from './imageFormats'

describe('image format helpers', () => {
  it('detects supported MIME types and filename extensions', () => {
    expect(formatFromMimeType('image/jpeg')).toBe('jpeg')
    expect(formatFromMimeType('image/png')).toBe('png')
    expect(formatFromFilename('holiday.JPEG')).toBe('jpeg')
    expect(formatFromFilename('image.webp')).toBe('webp')
    expect(formatFromFilename('document.svg')).toBeUndefined()
  })

  it('detects supported binary signatures', () => {
    expect(formatFromHeader(new Uint8Array([0xff, 0xd8, 0xff, 0x00]))).toBe('jpeg')
    expect(formatFromHeader(new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))).toBe('png')
    expect(formatFromHeader(new TextEncoder().encode('RIFF1234WEBP'))).toBe('webp')
    expect(formatFromHeader(new TextEncoder().encode('<svg></svg>'))).toBeUndefined()
  })

  it('maps output formats to MIME types and extensions', () => {
    expect(mimeTypeForFormat('jpeg')).toBe('image/jpeg')
    expect(extensionForFormat('jpeg')).toBe('jpg')
    expect(mimeTypeForFormat('webp')).toBe('image/webp')
  })

  it('requires an opaque background only for JPEG', () => {
    expect(requiresOpaqueBackground('jpeg')).toBe(true)
    expect(requiresOpaqueBackground('png')).toBe(false)
    expect(requiresOpaqueBackground('webp')).toBe(false)
  })
})
