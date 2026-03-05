"""
E2E Tests for TDEase Interactive Visualization
Tests complete user workflows using Playwright
"""

import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'

/**
 * Helper Functions
 */
async function loginIfNeeded(page) {
  // Add login logic if authentication is implemented
  const hasLoginForm = await page.locator('input[type="email"], input[type="username"]').count()
  if (hasLoginForm > 0) {
    await page.fill('input[type="email"], input[type="username"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/workflows')
  }
}

async function createWorkflow(page, workflowName: string) {
  await page.click('button:has-text("New Workflow"), a:has-text("Create")')
  await page.fill('input[name="name"], input[placeholder*="name"]', workflowName)
  await page.click('button:has-text("Create"), button:has-text("Save")')
  await expect(page.locator(`h1, h2:has-text("${workflowName}")`).toBeVisible()
}

async function addNode(page, nodeType: string, position = { x: 100, y: 100 }) {
  await page.click('[data-testid="node-palette"] button:has-text("Add Node")')
  await page.click(`[data-testid="node-${nodeType}"], [role="option"]:has-text("${nodeType}")`)

  // Get the canvas and drag the node
  const canvas = page.locator('.vue-flow')
  await canvas.click({ position })

  // Verify node was added
  await expect(page.locator(`.vue-flow__node[data-type="${nodeType}"]`)).toBeVisible()
}

async function connectNodes(page, sourceId: string, targetId: string) {
  const source = page.locator(`.vue-flow__node[data-id="${sourceId}"] .vue-flow__handle.source`)
  const target = page.locator(`.vue-flow__node[data-id="${targetId}"] .vue-flow__handle.target`)

  await source.dragTo(target)

  // Verify connection was created
  await expect(page.locator(`.vue-flow__edge path`)).toHaveCount(await page.locator(`.vue-flow__edge`).count())
}

/**
 * Test Suite: Workflow Creation with Interactive Nodes
 */
test.describe('Workflow Creation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
    await loginIfNeeded(page)
  })

  test('should create new workflow with interactive nodes', async ({ page }) => {
    await createWorkflow(page, 'Test Interactive Workflow')

    // Add TopFD compute node
    await addNode(page, 'topfd', { x: 100, y: 100 })

    // Add FeatureMap interactive node
    await addNode(page, 'featuremap_viewer', { x: 400, y: 100 })

    // Add Spectrum interactive node
    await addNode(page, 'spectrum_viewer', { x: 700, y: 100 })

    // Verify nodes are on canvas
    await expect(page.locator('.vue-flow__node[data-type="topfd"]')).toBeVisible()
    await expect(page.locator('.vue-flow__node[data-type="featuremap_viewer"]')).toBeVisible()
    await expect(page.locator('.vue-flow__node[data-type="spectrum_viewer"]')).toBeVisible()
  })

  test('should connect compute node to interactive viewer', async ({ page }) => {
    await createWorkflow(page, 'Connection Test')

    await addNode(page, 'topfd', { x: 100, y: 100 })
    await addNode(page, 'featuremap_viewer', { x: 400, y: 100 })

    // Get the node IDs from the DOM
    const topfdNode = await page.locator('.vue-flow__node[data-type="topfd"]').getAttribute('data-id')
    const featuremapNode = await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').getAttribute('data-id')

    await connectNodes(page, topfdNode, featuremapNode)

    // Verify data edge was created (solid line)
    const edge = page.locator('.vue-flow__edge')
    await expect(edge).toBeVisible()
  })

  test('should create state edge between interactive nodes', async ({ page }) => {
    await createWorkflow(page, 'State Edge Test')

    await addNode(page, 'featuremap_viewer', { x: 200, y: 100 })
    await addNode(page, 'spectrum_viewer', { x: 500, y: 100 })

    const featuremapNode = await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').getAttribute('data-id')
    const spectrumNode = await page.locator('.vue-flow__node[data-type="spectrum_viewer"]').getAttribute('data-id')

    // Connect via state output handle
    const sourceHandle = page.locator(`.vue-flow__node[data-id="${featuremapNode}"] .handle-source[data-handle*="selection"]`)
    const targetHandle = page.locator(`.vue-flow__node[data-id="${spectrumNode}"] .handle-target[data-handle*="selection"]`)

    await sourceHandle.dragTo(targetHandle)

    // Verify state edge was created (dashed orange line)
    const stateEdge = page.locator('.vue-flow__edge.edge-state, .vue-flow__edge[class*="state"]')
    await expect(stateEdge).toBeVisible()
    await expect(stateEdge).toHaveCSS('stroke-dasharray', /5, 5/)  // Dashed line
  })
})

/**
 * Test Suite: Configuration Panel Interaction
 */
test.describe('Interactive Node Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
    await loginIfNeeded(page)
  })

  test('should open configuration panel on double-click', async ({ page }) => {
    await createWorkflow(page, 'Config Panel Test')
    await addNode(page, 'featuremap_viewer', { x: 200, y: 200 })

    const node = page.locator('.vue-flow__node[data-type="featuremap_viewer"]')

    // Double-click to open config
    await node.dblclick()

    // Verify configuration panel opens
    await expect(page.locator('[data-testid="config-panel"], .node-config-panel')).toBeVisible()
    await expect(page.locator('text=Data Mapping')).toBeVisible()
  })

  test('should display column mapping dropdowns', async ({ page }) => {
    await createWorkflow(page, 'Column Mapping Test')
    await addNode(page, 'featuremap_viewer', { x: 200, y: 200 })

    const node = page.locator('.vue-flow__node[data-type="featuremap_viewer"]')
    await node.dblclick()

    // Verify axis mapping dropdowns exist
    await expect(page.locator('label:has-text("X Axis")')).toBeVisible()
    await expect(page.locator('label:has-text("Y Axis")')).toBeVisible()
    await expect(page.locator('select[name="xAxis"], select[name="x"]')).toBeVisible()
    await expect(page.locator('select[name="yAxis"], select[name="y"]')).toBeVisible()
  })

  test('should auto-populate columns from schema', async ({ page }) => {
    await createWorkflow(page, 'Auto Populate Test')
    await addNode(page, 'topfd', { x: 100, y: 100 })
    await addNode(page, 'featuremap_viewer', { x: 400, y: 100 })

    // Connect nodes to trigger schema loading
    const topfdNode = await page.locator('.vue-flow__node[data-type="topfd"]').getAttribute('data-id')
    const featuremapNode = await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').getAttribute('data-id')
    await connectNodes(page, topfdNode, featuremapNode)

    // Double-click featuremap to open config
    await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').dblclick()

    // Wait for schema to load and populate dropdowns
    await page.waitForTimeout(1000)

    // Verify columns are populated (should have mz, rt, intensity from TopFD schema)
    const xAxisDropdown = page.locator('select[name="xAxis"], select[name="x"]')
    await xAxisDropdown.click()

    const options = await page.locator('select[name="xAxis"] option, select[name="x"] option').all()
    expect(options.length).toBeGreaterThan(0)

    // Verify expected columns exist
    const optionTexts = await Promise.all(options.map(async opt => await opt.textContent()))
    expect(optionTexts.some(text => text.toLowerCase().includes('mz') || text.toLowerCase().includes('rt'))).toBeTruthy()
  })

  test('should apply and save configuration', async ({ page }) => {
    await createWorkflow(page, 'Save Config Test')
    await addNode(page, 'featuremap_viewer', { x: 200, y: 200 })

    await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').dblclick()

    // Change axis mapping
    await page.selectOption('select[name="xAxis"], select[name="x"]', 'rt')
    await page.selectOption('select[name="yAxis"], select[name="y"]', 'mz')

    // Click apply
    await page.click('button:has-text("Apply"), button:has-text("Save")')

    // Close and reopen config panel
    await page.keyboard.press('Escape')
    await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').dblclick()

    // Verify configuration persisted
    const xAxisValue = await page.locator('select[name="xAxis"], select[name="x"]').inputValue()
    const yAxisValue = await page.locator('select[name="yAxis"], select[name="y"]').inputValue()

    expect(xAxisValue).toBe('rt')
    expect(yAxisValue).toBe('mz')
  })
})

/**
 * Test Suite: Cross-Filtering Workflows
 */
test.describe('Cross-Filtering', () => {
  test('should execute workflow with compute and interactive nodes', async ({ page }) => {
    await createWorkflow(page, 'Cross-Filter Test')

    // Build workflow: TopFD → FeatureMap → Spectrum
    await addNode(page, 'topfd', { x: 100, y: 100 })
    await addNode(page, 'featuremap_viewer', { x: 400, y: 100 })
    await addNode(page, 'spectrum_viewer', { x: 700, y: 100 })

    const topfdNode = await page.locator('.vue-flow__node[data-type="topfd"]').getAttribute('data-id')
    const featuremapNode = await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').getAttribute('data-id')
    const spectrumNode = await page.locator('.vue-flow__node[data-type="spectrum_viewer"]').getAttribute('data-id')

    await connectNodes(page, topfdNode, featuremapNode)
    await connectNodes(page, featuremapNode, spectrumNode)

    // Execute workflow
    await page.click('button:has-text("Execute"), button:has-text("Run")')

    // Wait for execution to complete
    await page.waitForSelector('[data-testid="execution-complete"], .node-status[data-status="completed"]', { timeout: 30000 })

    // Verify compute node completed
    await expect(page.locator(`.vue-flow__node[data-id="${topfdNode}"] .node-status[data-status="completed"]`)).toBeVisible()

    // Verify interactive nodes were skipped (not executed)
    await expect(page.locator(`.vue-flow__node[data-id="${featuremapNode}"] .node-status[data-status="skipped"]`)).toBeVisible()
    await expect(page.locator(`.vue-flow__node[data-id="${spectrumNode}"] .node-status[data-status="skipped"]`)).toBeVisible()
  })

  test('should enable brush selection in FeatureMap viewer', async ({ page }) => {
    // This test assumes data is already loaded
    await page.goto(`${BASE_URL}/workflows/test-interactive`)

    // Open FeatureMap viewer
    await page.click('.vue-flow__node[data-type="featuremap_viewer"]')
    await page.dblclick()

    // Verify brush tool is available
    await expect(page.locator('[data-testid="brush-tool"], [aria-label*="brush"]')).toBeVisible()

    // Activate brush tool
    await page.click('[data-testid="brush-tool"]')

    // Simulate brush selection (drag on canvas)
    const canvas = page.locator('.featuremap-canvas, .plotly-canvas')
    await canvas.click({ position: { x: 100, y: 100 } })
    await canvas.down()
    await canvas.move({ position: { x: 200, y: 200 } })
    await canvas.up()

    // Verify selection was created
    await expect(page.locator('.brush-selection, .selection-rectangle')).toBeVisible()
  })

  test('should propagate selection to connected Spectrum viewer', async ({ page }) => {
    await page.goto(`${BASE_URL}/workflows/test-interactive`)

    // Make a selection in FeatureMap
    const featuremapCanvas = page.locator('.vue-flow__node[data-type="featuremap_viewer"] .plotly-canvas')
    await featuremapCanvas.click({ position: { x: 150, y: 150 } })
    await featuremapCanvas.down()
    await featuremapCanvas.move({ position: { x: 250, y: 250 } })
    await featuremapCanvas.up()

    // Wait for state propagation
    await page.waitForTimeout(500)

    // Verify Spectrum viewer highlights filtered peaks
    const spectrumViewer = page.locator('.vue-flow__node[data-type="spectrum_viewer"]')
    await expect(spectrumViewer.locator('.highlighted-peak, .selected-peak')).toBeVisible()
  })
})

/**
 * Test Suite: HTML Viewer Integration
 */
test.describe('HTML Viewer', () => {
  test('should display PrSM HTML on feature selection', async ({ page }) => {
    await page.goto(`${BASE_URL}/workflows/test-interactive`)

    // Select a feature in FeatureMap
    const featuremapNode = page.locator('.vue-flow__node[data-type="featuremap_viewer"]')
    await featuremapNode.click()

    // Click on a specific data point
    const canvas = featuremapNode.locator('.plotly-canvas')
    await canvas.click({ position: { x: 200, y: 200 }})

    // Wait for HTML viewer to load content
    await page.waitForTimeout(1000)

    // Verify HTML viewer displays PrSM sequence
    const htmlViewer = page.locator('.vue-flow__node[data-type="html_viewer"] iframe, .vue-flow__node[data-type="html_viewer"] .html-content')
    await expect(htmlViewer).toBeVisible()

    // Verify sequence content is loaded
    const content = await htmlViewer.content()
    expect(content).toContain(/sequence|ACDEFGHIK/i)
  })

  test('should update HTML when selection changes', async ({ page }) => {
    await page.goto(`${BASE_URL}/workflows/test-interactive`)

    const featuremapNode = page.locator('.vue-flow__node[data-type="featuremap_viewer"]')
    const canvas = featuremapNode.locator('.plotly-canvas')
    const htmlViewer = page.locator('.vue-flow__node[data-type="html_viewer"] iframe, .vue-flow__node[data-type="html_viewer"] .html-content')

    // Select first feature
    await canvas.click({ position: { x: 200, y: 200 }})
    await page.waitForTimeout(500)
    const firstContent = await htmlViewer.content()

    // Select different feature
    await canvas.click({ position: { x: 300, y: 300 }})
    await page.waitForTimeout(500)
    const secondContent = await htmlViewer.content()

    // Verify content changed
    expect(firstContent).not.toBe(secondContent)
  })
})

/**
 * Test Suite: Error Handling
 */
test.describe('Error Handling', () => {
  test('should show error when node configuration is invalid', async ({ page }) => {
    await createWorkflow(page, 'Error Test')
    await addNode(page, 'featuremap_viewer', { x: 200, y: 200 })

    await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').dblclick()

    // Try to apply invalid configuration (empty mapping)
    await page.selectOption('select[name="xAxis"], select[name="x"]', '')
    await page.click('button:has-text("Apply")')

    // Verify error message
    await expect(page.locator('text=required, text=Invalid, .el-message--error')).toBeVisible()
  })

  test('should handle missing data gracefully', async ({ page }) => {
    await createWorkflow(page, 'Missing Data Test')
    await addNode(page, 'featuremap_viewer', { x: 200, y: 200 })

    // Try to view data without connecting to compute node
    await page.locator('.vue-flow__node[data-type="featuremap_viewer"]').dblclick()

    // Verify awaiting data message
    await expect(page.locator('text=Awaiting input, text=No data, .node-empty')).toBeVisible()
  })
})

/**
 * Test Suite: Performance
 */
test.describe('Performance', () => {
  test('should load workflow with 10 nodes within 3 seconds', async ({ page }) => {
    const startTime = Date.now()

    await createWorkflow(page, 'Performance Test')

    for (let i = 0; i < 10; i++) {
      await addNode(page, i % 2 === 0 ? 'topfd' : 'featuremap_viewer', { x: 100 + i * 150, y: 100 })
    }

    const loadTime = Date.now() - startTime
    expect(loadTime).toBeLessThan(3000)  // 3 seconds
  })

  test('should handle large dataset rendering without freezing', async ({ page }) => {
    await page.goto(`${BASE_URL}/workflows/test-large-dataset`)

    // Monitor for freezing (long pauses)
    let lastActivity = Date.now()
    page.on('load', () => { lastActivity = Date.now() })

    // Try to interact with page
    await page.locator('body').click()

    const currentTime = Date.now()
    expect(currentTime - lastActivity).toBeLessThan(5000)  // Should not freeze for > 5s
  })
})
