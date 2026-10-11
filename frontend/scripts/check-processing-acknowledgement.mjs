// Optional real-browser integration test. Requires an existing Playwright install
// (no application dependency). Pass its absolute package path as argument 1.
// Starts only a loopback Vite server; all API requests are intercepted locally.
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
const require = createRequire(import.meta.url)
const { chromium } = require(process.argv[2] || 'playwright')
const cwd = fileURLToPath(new URL('..', import.meta.url))
const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '4179', '--strictPort'], {
  cwd, env: { ...process.env, VITE_API_BASE_URL: 'https://api.example.test' }, windowsHide: true, stdio: 'pipe',
})
let browser
let cases = 0
const origin = 'http://127.0.0.1:4179'
const png = { name: 'fixture.png', mimeType: 'image/png', buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==', 'base64') }
const pdf = { name: 'fixture.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-harmless mock fixture') }
const fixture = (name) => ({ name, mimeType: 'application/octet-stream', buffer: Buffer.from('harmless') })
try {
  await new Promise((resolve, reject) => {
    server.stdout.on('data', data => { if (data.toString().includes('4179')) resolve() })
    server.on('error', reject)
    server.on('exit', code => reject(new Error('Vite exited: ' + code)))
    const timer = setTimeout(() => reject(new Error('Vite startup timeout')), 15000)
    timer.unref()
  })
  browser = await chromium.launch({ channel: process.env.ACK_BROWSER_CHANNEL || 'msedge', headless: true })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  const requests = []
  let failNext = false
  await page.route('https://api.example.test/**', async route => {
    requests.push(new URL(route.request().url()).pathname)
    const inspect = route.request().url().includes('inspect-metadata') || route.request().url().includes('/metadata/inspect')
    await route.fulfill({ status: failNext ? 429 : 200, contentType: inspect || failNext ? 'application/json' : 'application/octet-stream',
      body: failNext ? JSON.stringify({ detail: 'Mock busy error' }) : inspect ? JSON.stringify({ fields: [] }) : 'harmless result' })
    failNext = false
  })
  const section = heading => page.locator('section').filter({ has: page.getByRole('heading', { name: heading, exact: true }) })
  // Intentional test-only bypass of disabled DOM styling: invokes the real React
  // handler, proving the guard is not merely an HTML disabled attribute.
  const bypass = async button => button.evaluate(node => {
    const key = Object.keys(node).find(key => key.startsWith('__reactProps'))
    node[key].onClick()
  })
  const checkFlow = async (tool, input, action, path) => {
    const checkbox = tool.getByRole('checkbox')
    assert.equal(await checkbox.count(), 1)
    assert.equal(await checkbox.isChecked(), false)
    await tool.locator('input[type=file]').setInputFiles(input)
    const count = requests.length
    assert.equal(await action.getAttribute('type'), 'button')
    assert.equal(await action.evaluate(node => node.closest('form') === null), true)
    const dropped = await page.evaluateHandle(() => { const data = new DataTransfer(); data.items.add(new File(['harmless drop'], 'dropped.pdf')); return data })
    await tool.dispatchEvent('drop', { dataTransfer: dropped })
    await dropped.dispose()
    assert.equal(requests.length, count)
    assert.equal(await action.isDisabled(), true)
    await action.dispatchEvent('click')
    await action.dispatchEvent('keydown', { key: 'Enter' })
    await bypass(action)
    await tool.getByRole('alert').waitFor()
    assert.equal(requests.length, count)
    assert.equal(await tool.getByRole('link', { name: 'Terms of Service' }).getAttribute('href'), '/terms')
    assert.equal(await tool.getByRole('link', { name: 'Privacy Policy' }).getAttribute('href'), '/privacy')
    await checkbox.focus()
    await page.keyboard.press('Space')
    assert.equal(await checkbox.isChecked(), true)
    await action.focus()
    const responsePromise = page.waitForResponse(response => response.url().endsWith(path))
    await page.keyboard.press('Enter')
    await responsePromise
    assert.equal(requests.at(-1), path)
    if (!path.includes('inspect')) await tool.getByRole('button', { name: /Download/ }).waitFor()
    else await action.waitFor({ state: 'visible' })
    await tool.locator('input[type=file]').setInputFiles(input)
    assert.equal(await checkbox.isChecked(), false)
    assert.equal(await action.isDisabled(), true)
    cases++
  }
  await page.goto(origin + '/convert')
  for (const [heading, input, name, path] of [
    ['Advanced image converter', fixture('fixture.heic'), 'Upload and convert', '/images/convert'],
    ['Remove background', png, 'Upload and remove background', '/images/remove-background'],
    ['Document converter', fixture('fixture.docx'), 'Convert document', '/documents/convert'],
    ['Spreadsheet and presentation converter', fixture('fixture.xlsx'), 'Convert file', '/office/convert'],
  ]) {
    const tool = section(heading)
    await checkFlow(tool, input, tool.getByRole('button', { name, exact: true }), path)
  }
  const background = section('Remove background')
  await background.getByRole('checkbox').check()
  await background.getByRole('combobox').selectOption('webp')
  assert.equal(await background.getByRole('checkbox').isChecked(), false)
  await background.getByRole('checkbox').check()
  failNext = true
  await background.getByRole('button', { name: 'Upload and remove background' }).click()
  await background.getByText('Mock busy error', { exact: true }).waitFor()
  await background.locator('input[type=file]').setInputFiles({ ...png, name: 'replacement.png' })
  assert.equal(await background.getByRole('checkbox').isChecked(), false)
  cases++
  // Legal links must not submit or discard the current selection.
  const beforeLink = requests.length
  const popupPromise = page.waitForEvent('popup')
  await background.getByRole('link', { name: 'Terms of Service' }).click()
  const popup = await popupPromise
  await popup.waitForLoadState()
  assert.ok(popup.url().endsWith('/terms'))
  await popup.close()
  assert.equal(requests.length, beforeLink)
  assert.equal(await background.locator('input[type=file]').evaluate(node => node.files[0].name), 'replacement.png')
  cases++

  await page.goto(origin + '/pdf-tools')
  const tool = section('PDF toolkit')
  for (const operation of ['merge', 'extract', 'split', 'reorder', 'delete-pages', 'to-images', 'images-to-pdf', 'remove-metadata', 'optimize', 'inspect-metadata']) {
    await tool.getByRole('combobox').selectOption(operation)
    const input = operation === 'images-to-pdf' ? [png, { ...png, name: 'second.png' }]
      : operation === 'merge' ? [pdf, { ...pdf, name: 'second.pdf' }] : pdf
    await checkFlow(tool, input, tool.getByRole('button', { name: 'Process PDF' }), '/pdf/' + operation)
    assert.equal(await tool.getByRole('checkbox').isChecked(), false)
  }
  await page.goto(origin + '/metadata')
  const metadata = section('Metadata inspector and privacy tools')
  await checkFlow(metadata, png, metadata.getByRole('button', { name: 'Inspect metadata', exact: true }), '/metadata/inspect')
  await metadata.getByRole('checkbox').check()
  await metadata.getByRole('radio', { name: 'Remove supported metadata' }).check()
  assert.equal(await metadata.getByRole('checkbox').isChecked(), false)
  await checkFlow(metadata, png, metadata.getByRole('button', { name: 'Remove supported metadata', exact: true }), '/metadata/remove')
  // Leaving and returning does not retain acceptance.
  await metadata.getByRole('checkbox').check()
  await page.goto(origin + '/convert')
  assert.equal(await section('Remove background').getByRole('checkbox').isChecked(), false)
  const beforeLocal = requests.length
  const local = section('Image privacy tool')
  assert.equal(await local.getByRole('checkbox').count(), 0)
  const droppedImage = await page.evaluateHandle(base64 => {
    const bytes = Uint8Array.from(atob(base64), character => character.charCodeAt(0))
    const data = new DataTransfer(); data.items.add(new File([bytes], 'dropped.png', { type: 'image/png' })); return data
  }, png.buffer.toString('base64'))
  await local.locator('div.relative').dispatchEvent('drop', { dataTransfer: droppedImage })
  await droppedImage.dispose()
  await local.getByRole('button', { name: 'Process image locally', exact: true }).click()
  await local.getByRole('button', { name: 'Download file', exact: true }).waitFor()
  const batch = section('Batch image conversion')
  assert.equal(await batch.getByRole('checkbox').count(), 0)
  await batch.locator('input[type=file]').setInputFiles([png, { ...png, name: 'second.png' }])
  await batch.getByRole('button', { name: 'Convert batch locally' }).click()
  await page.waitForFunction(() => document.querySelectorAll('li').length && [...document.querySelectorAll('li')].filter(node => node.textContent.includes('complete')).length === 2)
  assert.equal(requests.length, beforeLocal)
  cases += 2
  for (const width of [320, 390, 1280]) {
    await page.setViewportSize({ width, height: 900 })
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
    const acknowledgement = section('Remove background').locator('.processing-acknowledgement')
    await acknowledgement.scrollIntoViewIfNeeded()
    const bounds = await acknowledgement.boundingBox()
    assert.ok(bounds && bounds.x >= 0 && bounds.x + bounds.width <= width)
    await section('Remove background').getByRole('checkbox').focus()
    assert.equal(await section('Remove background').getByRole('checkbox').evaluate(node => node === document.activeElement), true)
    cases++
  }
  assert.equal(await page.evaluate(() => localStorage.length), 0)
  console.log(`PASS: ${cases} real-browser acknowledgement/local-processing cases; all API traffic mocked.`)
} finally {
  await browser?.close()
  server.kill()
}
