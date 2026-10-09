import { describe, expect, it } from 'vitest'
import {
  conversionCapability,
  formatFromExtension,
  formatFromFilename,
  formatFromMimeType,
  formatsForMode,
  normalizeFormat,
} from './registry'

describe('format registry', () => {
  it('normalizes extensions and MIME aliases', () => {
    expect(normalizeFormat('JPG')?.id).toBe('jpeg')
    expect(formatFromExtension('.jpeg')?.id).toBe('jpeg')
    expect(formatFromFilename('../photos/image.PNG')?.id).toBe('png')
    expect(formatFromMimeType('image/pjpeg')?.id).toBe('jpeg')
  })

  it('exposes only implemented local formats', () => {
    expect(formatsForMode('local', 'image').map((format) => format.id)).toEqual([
      'jpeg',
      'png',
      'webp',
    ])
    expect(normalizeFormat('docx')?.implemented).toBe(true)
    expect(formatsForMode('local', 'document')).toEqual([])
    expect(normalizeFormat('heic')?.executionModes).toEqual(['server'])
    expect(normalizeFormat('jpeg')?.operationModes?.inspectMetadata).toEqual(['server'])
    expect(normalizeFormat('jpeg')?.operationModes?.removeMetadata).toEqual(['local', 'server'])
  })

  it('checks explicit conversion edges and execution modes', () => {
    expect(conversionCapability('png', 'webp', 'local')?.target).toBe('webp')
    expect(conversionCapability('docx', 'pdf', 'server')?.target).toBe('pdf')
    expect(conversionCapability('docx', 'pdf', 'local')).toBeUndefined()
    expect(conversionCapability('png', 'pdf', 'local')).toBeUndefined()
  })
})
