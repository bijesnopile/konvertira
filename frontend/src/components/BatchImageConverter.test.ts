import { describe, expect, it, vi } from 'vitest'
import { runLocalImageBatch } from './BatchImageConverter'

describe('local batch processing', () => {
  it('continues after an item error and processes sequentially', async () => {
    const files = [new File(['a'], 'a.png'), new File(['b'], 'b.png')]
    const updates: Array<[number, string]> = []
    let active = 0
    let maxActive = 0
    const processor = vi.fn(async (file: File) => {
      active += 1
      maxActive = Math.max(maxActive, active)
      active -= 1
      if (file.name === 'a.png') throw new Error('bad image')
      return { blob: new Blob(['ok']), filename: 'b.jpg', mimeType: 'image/jpeg' as const, format: 'jpeg' as const, size: 2, width: 1, height: 1, processingMode: 'local' as const }
    })

    await runLocalImageBatch(files, 'jpeg', (index, update) => updates.push([index, update.status]), processor)

    expect(updates).toEqual([[0, 'processing'], [0, 'failed'], [1, 'processing'], [1, 'complete']])
    expect(maxActive).toBe(1)
    expect(processor).toHaveBeenCalledTimes(2)
  })
})
