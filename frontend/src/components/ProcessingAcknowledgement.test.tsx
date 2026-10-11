import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { ProcessingAcknowledgement } from './ProcessingAcknowledgement'
import { BackgroundRemoval } from './BackgroundRemoval'
import { DocumentConverter } from './DocumentConverter'
import { OfficeConverter } from './OfficeConverter'
import { ServerImageConverter } from './ServerImageConverter'
import { PdfToolkit } from './PdfToolkit'
import { MetadataPrivacyTool } from './MetadataPrivacyTool'
import { ToolCard } from './ToolCard'
import { BatchImageConverter } from './BatchImageConverter'
import { sameProcessingScope } from '../hooks/useProcessingAcknowledgement'

// A synchronous hook host lets tests call the *actual component event handlers*,
// including disabled-button bypass, without adding a DOM/testing dependency.
// Real DOM/keyboard/drag-drop checks live in scripts/check-processing-acknowledgement.mjs.
const host = vi.hoisted(() => ({ slots: [] as unknown[], cursor: 0, dirty: false }))
vi.mock('react', async (original) => {
  const react = await original<typeof import('react')>()
  return { ...react, useRef: (initial: unknown) => {
    const index = host.cursor++
    if (!(index in host.slots)) host.slots[index] = { current: initial }
    return host.slots[index]
  }, useState: (initial: unknown) => {
    const index = host.cursor++
    if (!(index in host.slots)) host.slots[index] = typeof initial === 'function' ? initial() : initial
    return [host.slots[index], (value: unknown) => {
      host.slots[index] = typeof value === 'function' ? value(host.slots[index]) : value
      host.dirty = true
    }]
  } }
})

type Element = ReactElement<Record<string, any>>
function elements(tree: unknown): Element[] {
  if (Array.isArray(tree)) return tree.flatMap(elements)
  if (!tree || typeof tree !== 'object' || !('props' in tree)) return []
  const node = tree as Element
  return [node, ...elements(node.props.children)]
}
function mount(Component: () => ReactElement) {
  let tree: ReactElement
  const render = () => {
    do { host.cursor = 0; host.dirty = false; tree = Component() } while (host.dirty)
  }
  render()
  return {
    nodes: () => elements(tree),
    render,
    acknowledgement: () => elements(tree).find((node) => node.type === ProcessingAcknowledgement)!,
    fileInput: () => elements(tree).find((node) => node.type === 'input' && node.props.type === 'file')!,
    action: () => elements(tree).find((node) => node.type === 'button' && node.props.disabled !== undefined && node.props.onClick)!,
    choose(files: File[]) {
      this.fileInput().props.onChange({ target: { files, value: 'fixture' } })
      render()
    },
    accept() { this.acknowledgement().props.setAccepted(true); render() },
  }
}

beforeEach(() => {
  host.slots = []; host.cursor = 0; host.dirty = false
  vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ fields: [] }), {
    headers: { 'Content-Type': 'application/json' },
  })))
})
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs() })

describe('website server-processing acknowledgement', () => {
  for (const [Component, filename, path] of [
    [BackgroundRemoval, 'fixture.png', '/images/remove-background'],
    [ServerImageConverter, 'fixture.heic', '/images/convert'],
    [DocumentConverter, 'fixture.docx', '/documents/convert'],
    [OfficeConverter, 'fixture.xlsx', '/office/convert'],
    [PdfToolkit, 'fixture.pdf', '/pdf/merge'],
    [MetadataPrivacyTool, 'fixture.png', '/metadata/inspect'],
  ] as const) {
    it(`${Component.name} guards actual handler and resets for replacement files`, async () => {
      const app = mount(Component)
      expect(app.acknowledgement().props.accepted).toBe(false)
      app.choose([new File(['harmless'], filename)])
      expect(app.action().props.disabled).toBe(true)
      await app.action().props.onClick()
      app.render()
      expect(fetch).not.toHaveBeenCalled()
      expect(app.acknowledgement().props.error).toBe(true)
      app.accept()
      expect(app.action().props.disabled).toBe(false)
      await app.action().props.onClick()
      await vi.waitFor(() => expect(fetch).toHaveBeenCalledOnce())
      expect(String(vi.mocked(fetch).mock.calls[0][0]).endsWith(path)).toBe(true)
      app.choose([new File(['replacement'], filename)])
      expect(app.acknowledgement().props.accepted).toBe(false)
      await app.action().props.onClick()
      expect(fetch).toHaveBeenCalledOnce()
    })
  }
  for (const operation of ['merge', 'extract', 'split', 'reorder', 'delete-pages', 'to-images', 'images-to-pdf', 'inspect-metadata', 'remove-metadata', 'optimize']) {
    it(`guards PDF ${operation}, including alternate and multiple-file actions`, async () => {
      const app = mount(PdfToolkit)
      app.nodes().find(node => node.type === 'select')!.props.onChange({ target: { value: operation } }); app.render()
      const multiple = operation === 'merge' || operation === 'images-to-pdf'
      const files = [new File(['first'], 'first.pdf'), ...(multiple ? [new File(['second'], 'second.pdf')] : [])]
      app.choose(files)
      await app.action().props.onClick()
      expect(fetch).not.toHaveBeenCalled()
      app.accept(); await app.action().props.onClick()
      await vi.waitFor(() => expect(fetch).toHaveBeenCalledOnce())
      const request = vi.mocked(fetch).mock.calls[0]
      expect(String(request[0]).endsWith('/pdf/' + operation)).toBe(true)
      expect((request[1]?.body as FormData).getAll(multiple ? 'files' : 'file')).toHaveLength(files.length)
    })
  }
  it('does not revive acceptance when switching away and back to an operation', () => {
    const app = mount(BackgroundRemoval)
    app.choose([new File(['fixture'], 'source.png')]); app.accept()
    const select = () => app.nodes().find(node => node.type === 'select')!
    select().props.onChange({ target: { value: 'webp' } }); app.render()
    expect(app.acknowledgement().props.accepted).toBe(false)
    select().props.onChange({ target: { value: 'png' } }); app.render()
    expect(app.acknowledgement().props.accepted).toBe(false)
  })
  it('requires fresh acceptance when switching metadata inspection to removal', async () => {
    const app = mount(MetadataPrivacyTool)
    app.choose([new File(['fixture'], 'fixture.png')]); app.accept()
    app.nodes().find(node => node.props.type === 'radio' && node.props.value === 'remove')!.props.onChange()
    app.render()
    expect(app.acknowledgement().props.accepted).toBe(false)
    await app.action().props.onClick()
    expect(fetch).not.toHaveBeenCalled()
    app.accept(); await app.action().props.onClick()
    await vi.waitFor(() => expect(fetch).toHaveBeenCalledOnce())
    expect(String(vi.mocked(fetch).mock.calls[0][0]).endsWith('/metadata/remove')).toBe(true)
  })
  it('scopes PDF acceptance to all files and the selected operation', () => {
    const app = mount(PdfToolkit)
    const first = new File(['first'], 'first.pdf'), second = new File(['second'], 'second.pdf')
    app.choose([first, second]); app.accept(); app.choose([second, first])
    expect(app.acknowledgement().props.accepted).toBe(false)
    app.accept()
    app.nodes().find(node => node.type === 'select')!.props.onChange({ target: { value: 'optimize' } })
    app.render()
    expect(app.acknowledgement().props.accepted).toBe(false)
  })
  it('does not grant acceptance to a replacement after errors', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('offline'))
    const app = mount(BackgroundRemoval)
    app.choose([new File(['first'], 'first.png')]); app.accept()
    await app.action().props.onClick()
    await vi.waitFor(() => expect(fetch).toHaveBeenCalledOnce())
    app.choose([new File(['next'], 'next.png')])
    expect(app.acknowledgement().props.accepted).toBe(false)
    await app.action().props.onClick()
    expect(fetch).toHaveBeenCalledOnce()
  })
  it('starts fresh after an unrelated visit', () => {
    const app = mount(BackgroundRemoval)
    app.choose([new File(['fixture'], 'source.png')]); app.accept()
    host.slots = []
    expect(mount(BackgroundRemoval).acknowledgement().props.accepted).toBe(false)
  })
  it('keeps both local-only components free of acknowledgement and uploads', () => {
    expect(mount(ToolCard).acknowledgement()).toBeUndefined()
    host.slots = []
    expect(mount(BatchImageConverter).acknowledgement()).toBeUndefined()
    expect(fetch).not.toHaveBeenCalled()
  })
  it('compares execution mode and File identity, not filenames', () => {
    const file = new File(['fixture'], 'same.png')
    expect(sameProcessingScope([file], 'server:convert', [file], 'server:convert')).toBe(true)
    expect(sameProcessingScope([file], 'server:convert', [file], 'local:convert')).toBe(false)
    expect(sameProcessingScope([file], 'server:convert', [new File(['other'], 'same.png')], 'server:convert')).toBe(false)
  })
  it('renders a labelled native checkbox, local legal links and accessible error', () => {
    const html = renderToStaticMarkup(<ProcessingAcknowledgement accepted={false} setAccepted={() => {}} error />)
    for (const phrase of ['type="checkbox"', 'href="/terms"', 'href="/privacy"', 'role="alert"', 'aria-describedby=', 'focus-visible', 'min-w-0']) expect(html).toContain(phrase)
    expect(html).not.toContain('checked=""')
  })
})
