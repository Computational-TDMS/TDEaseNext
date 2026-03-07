import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getTopMSVPrsmData } from './workspace-data'
import { ValidationError } from '../../types/errors'

type MockClient = {
  get: ReturnType<typeof vi.fn>
}

describe('workspace-data getTopMSVPrsmData', () => {
  let client: MockClient

  beforeEach(() => {
    client = {
      get: vi.fn(),
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests workflow-level interactive endpoint first when workflow_id is provided', async () => {
    const payload = { prsm_id: 7, workflow_id: 'wf_1' }
    client.get.mockResolvedValueOnce({ data: payload })

    const result = await getTopMSVPrsmData(client as any, {
      workflow_id: 'wf_1',
      node_id: 'toppic_1',
      prsm_id: 7,
      port_id: 'html_folder',
      sample: 'sample_a',
      spectrum_id: 66,
    })

    expect(result).toEqual(payload)
    expect(client.get).toHaveBeenCalledTimes(1)
    expect(client.get).toHaveBeenCalledWith(
      '/api/workflows/wf_1/nodes/toppic_1/interactive-data/7',
      {
        resolver: 'topmsv_prsm',
        port_id: 'html_folder',
        sample: 'sample_a',
        spectrum_id: 66,
      }
    )
  })

  it('falls back to execution endpoint when workflow-level request fails and execution_id exists', async () => {
    const workflowError = new Error('workflow interactive endpoint failed')
    const payload = { prsm_id: 7, execution_id: 'exec_1' }
    client.get.mockRejectedValueOnce(workflowError)
    client.get.mockResolvedValueOnce({ data: payload })

    const result = await getTopMSVPrsmData(client as any, {
      workflow_id: 'wf_1',
      execution_id: 'exec_1',
      node_id: 'toppic_1',
      prsm_id: 7,
      port_id: 'html_folder',
      spectrum_id: 66,
    })

    expect(result).toEqual(payload)
    expect(client.get).toHaveBeenCalledTimes(2)
    expect(client.get).toHaveBeenNthCalledWith(
      1,
      '/api/workflows/wf_1/nodes/toppic_1/interactive-data/7',
      {
        resolver: 'topmsv_prsm',
        port_id: 'html_folder',
        spectrum_id: 66,
      }
    )
    expect(client.get).toHaveBeenNthCalledWith(
      2,
      '/api/executions/exec_1/nodes/toppic_1/topmsv/prsm/7',
      {
        port_id: 'html_folder',
        spectrum_id: 66,
      }
    )
  })

  it('rethrows workflow request error when execution fallback is unavailable', async () => {
    const workflowError = new Error('workflow interactive endpoint failed')
    client.get.mockRejectedValueOnce(workflowError)

    await expect(
      getTopMSVPrsmData(client as any, {
        workflow_id: 'wf_1',
        node_id: 'toppic_1',
        prsm_id: 7,
      })
    ).rejects.toThrow('workflow interactive endpoint failed')

    expect(client.get).toHaveBeenCalledTimes(1)
  })

  it('throws validation error when neither workflow_id nor execution_id is provided', async () => {
    await expect(
      getTopMSVPrsmData(client as any, {
        node_id: 'toppic_1',
        prsm_id: 7,
      })
    ).rejects.toBeInstanceOf(ValidationError)
  })
})
