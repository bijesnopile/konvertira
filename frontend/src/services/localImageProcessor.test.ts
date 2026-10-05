import { describe, expect, it } from 'vitest'
import { JPEG_BACKGROUND_COLOR, qualityPercentToCanvas } from './localImageProcessor'

describe('local image processor helpers', () => {
  it('maps UI quality percentages to canvas quality', () => {
    expect(qualityPercentToCanvas(90)).toBe(0.9)
    expect(qualityPercentToCanvas(5)).toBe(0.1)
    expect(qualityPercentToCanvas(150)).toBe(1)
  })

  it('uses a white JPEG transparency background', () => {
    expect(JPEG_BACKGROUND_COLOR).toBe('#ffffff')
  })
})
