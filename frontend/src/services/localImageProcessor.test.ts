import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  calculateLocalResizeDimensions,
  JPEG_BACKGROUND_COLOR,
  processImageLocally,
  qualityPercentToCanvas,
} from './localImageProcessor'

describe('local image processor helpers', () => {
  afterEach(() => vi.unstubAllGlobals())
  it('maps UI quality percentages to canvas quality', () => {
    expect(qualityPercentToCanvas(90)).toBe(0.9)
    expect(qualityPercentToCanvas(5)).toBe(0.1)
    expect(qualityPercentToCanvas(150)).toBe(1)
  })

  it('uses a white JPEG transparency background', () => {
    expect(JPEG_BACKGROUND_COLOR).toBe('#ffffff')
  })

  it('preserves aspect ratio and does not upscale by default', () => {
    expect(calculateLocalResizeDimensions(1200, 800, { width: 600 })).toEqual({ width: 600, height: 400 })
    expect(calculateLocalResizeDimensions(1200, 800, { width: 2400 })).toEqual({ width: 1200, height: 800 })
    expect(calculateLocalResizeDimensions(1200, 800, { scalePercent: 50 })).toEqual({ width: 600, height: 400 })
  })

  it('does not call the network during local processing', async () => {
    const fetchSpy = vi.fn()
    const close = vi.fn()
    const canvas = {
      width: 0,
      height: 0,
      getContext: () => ({ fillStyle: '', fillRect: vi.fn(), drawImage: vi.fn() }),
      toBlob: (callback: BlobCallback, type: string) => callback(new Blob(['result'], { type })),
    }
    vi.stubGlobal('fetch', fetchSpy)
    vi.stubGlobal('createImageBitmap', vi.fn(async () => ({ width: 8, height: 6, close })))
    vi.stubGlobal('document', { createElement: () => canvas })
    const header = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
    const file = new File([header], 'local.png', { type: 'image/png' })

    const result = await processImageLocally(file, { action: 'convert-image', outputFormat: 'png' })

    expect(result.processingMode).toBe('local')
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(close).toHaveBeenCalledOnce()
  })
})
