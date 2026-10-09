import { describe, expect, it } from 'vitest'
import { formatBytes, formatSizeDifference, safeOutputFilename } from './files'

describe('file presentation helpers', () => {
  it('formats file sizes', () => {
    expect(formatBytes(500)).toBe('500 B')
    expect(formatBytes(1536)).toBe('1.5 KB')
    expect(formatBytes(2 * 1024 * 1024)).toBe('2.0 MB')
  })

  it('creates safe local output filenames', () => {
    expect(safeOutputFilename('../private/photo?.png', 'jpg')).toBe('photo_.jpg')
    expect(safeOutputFilename('portrait.jpeg', 'jpg', '-clean')).toBe('portrait-clean.jpg')
    expect(safeOutputFilename('portrait.jpeg', 'jpeg')).toBe('portrait.jpg')
    expect(() => safeOutputFilename('clip.mp4', 'mp4')).toThrow('Unsupported output extension')
  })

  it('describes output-size differences', () => {
    expect(formatSizeDifference(750, 1000)).toBe('250 B smaller (25.0%)')
    expect(formatSizeDifference(1250, 1000)).toBe('250 B larger (25.0%)')
  })
})
