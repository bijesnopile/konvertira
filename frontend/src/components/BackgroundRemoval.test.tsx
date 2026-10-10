import { afterEach, describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { BackgroundRemoval } from './BackgroundRemoval'

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.resetModules() })

describe('server background removal', () => {
  it('explains upload before processing and labels the server operation', () => {
    const html = renderToStaticMarkup(<BackgroundRemoval />)
    expect(html).toContain('Server processing')
    expect(html).toContain('uploads the image to Konvertira')
    expect(html).toContain('Upload and remove background')
    expect(html).toContain('hair, fur')
  })

  it('uses the explicit server endpoint and returns a downloadable file', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')
    const fetch = vi.fn(async (_url: string, _request?: RequestInit) => new Response(new Blob(['result']), { headers: { 'Content-Disposition': 'attachment; filename="transparent.webp"', 'Content-Type': 'image/webp' } }))
    vi.stubGlobal('fetch', fetch)
    const { removeImageBackground } = await import('../services/api')
    const result = await removeImageBackground(new File(['source'], 'source.png'), 'webp')
    expect(fetch.mock.calls[0][0]).toBe('https://api.example.test/images/remove-background')
    const request = fetch.mock.calls[0][1] as RequestInit
    expect((request.body as FormData).get('output_format')).toBe('webp')
    expect(result.filename).toBe('transparent.webp')
    expect(await result.blob.text()).toBe('result')
  })

  it('propagates server errors for display', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ detail: 'Background removal is busy.' }), { status: 429, headers: { 'Content-Type': 'application/json' } })))
    const { removeImageBackground } = await import('../services/api')
    await expect(removeImageBackground(new File(['source'], 'source.png'))).rejects.toThrow('Background removal is busy.')
  })
})
