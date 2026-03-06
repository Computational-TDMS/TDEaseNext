/**
 * Property-based tests for APIClient
 * Feature: frontend-services, Property 1: API 请求 JSON 序列化往返一致性
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import fc from 'fast-check'
import { APIClient } from './client'

describe('APIClient', () => {
  let client: APIClient
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    client = new APIClient({
      baseURL: 'http://localhost:3000',
      timeout: 5000,
    })

    // Mock fetch
    fetchMock = vi.fn()
    ;(globalThis as any).fetch = fetchMock
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Property 1: API 请求 JSON 序列化往返一致性', () => {
    it('should preserve data structure through JSON serialization round-trip', async () => {
      /**
       * Feature: frontend-services, Property 1: API 请求 JSON 序列化往返一致性
       * Validates: Requirements 1.2
       *
       * For any valid JavaScript object, when sent through APIClient and received,
       * the deserialized response should maintain data structure consistency.
       * Note: JSON serialization converts undefined to null, which is expected behavior.
       */
      await fc.assert(
        fc.asyncProperty(
          fc.object({
            key: fc.string(),
            values: [
              fc.string(),
              fc.integer(),
              fc.boolean(),
              fc.array(fc.string()),
              fc.record({
                nested: fc.string(),
              })
            ],
          }),
          async (testData: any) => {
            // Setup mock response - use JSON.stringify to simulate actual serialization
            const serialized = JSON.stringify(testData)
            const deserialized = JSON.parse(serialized)
            
            const mockResponse = new Response(serialized, {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })

            fetchMock.mockResolvedValueOnce(mockResponse)

            // Send request
            const response = await client.post<typeof testData>('/test', testData)

            // Verify data structure is preserved after JSON round-trip
            // (undefined becomes null in JSON, which is expected)
            expect(response.data).toEqual(deserialized)
            expect(response.status).toBe(200)
            expect(typeof response.data).toBe('object')

            // Verify JSON serialization happened
            expect(fetchMock).toHaveBeenCalledWith(
              'http://localhost:3000/test',
              expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(testData),
              })
            )
          }
        ),
        { numRuns: 100 }
      )
    })

    it('should handle nested objects correctly', async () => {
      /**
       * Feature: frontend-services, Property 1: API 请求 JSON 序列化往返一致性
       * Validates: Requirements 1.2
       */
      const complexObject = {
        metadata: {
          id: 'test-123',
          timestamp: Date.now(),
          tags: ['tag1', 'tag2'],
        },
        data: {
          values: [1, 2, 3],
          nested: {
            deep: {
              value: 'test',
            },
          },
        },
      }

      const mockResponse = new Response(JSON.stringify(complexObject), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      const response = await client.post('/test', complexObject)

      expect(response.data).toEqual(complexObject)
      expect((response.data as any).metadata.id).toBe('test-123')
      expect((response.data as any).data.nested.deep.value).toBe('test')
    })

    it('should handle arrays of objects', async () => {
      /**
       * Feature: frontend-services, Property 1: API 请求 JSON 序列化往返一致性
       * Validates: Requirements 1.2
       */
      const arrayData = [
        { id: 1, name: 'item1' },
        { id: 2, name: 'item2' },
        { id: 3, name: 'item3' },
      ]

      const mockResponse = new Response(JSON.stringify(arrayData), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      const response = await client.post<typeof arrayData>('/test', arrayData)

      expect(Array.isArray(response.data)).toBe(true)
      expect(response.data).toHaveLength(3)
      expect(response.data[0]).toEqual({ id: 1, name: 'item1' })
    })

    it('should handle null and undefined values', async () => {
      /**
       * Feature: frontend-services, Property 1: API 请求 JSON 序列化往返一致性
       * Validates: Requirements 1.2
       */
      const dataWithNulls = {
        field1: 'value',
        field2: null,
        field3: 'another',
      }

      const mockResponse = new Response(JSON.stringify(dataWithNulls), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      const response = await client.post<typeof dataWithNulls>('/test', dataWithNulls)

      expect((response.data as any).field1).toBe('value')
      expect((response.data as any).field2).toBeNull()
      expect((response.data as any).field3).toBe('another')
    })
  })

  describe('APIClient basic functionality', () => {
    it('should make GET requests', async () => {
      const mockData = { id: 1, name: 'test' }
      const mockResponse = new Response(JSON.stringify(mockData), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      const response = await client.get('/test')

      expect(response.data).toEqual(mockData)
      expect(response.status).toBe(200)
      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:3000/test',
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('should make POST requests', async () => {
      const requestData = { name: 'test' }
      const responseData = { id: 1, ...requestData }
      const mockResponse = new Response(JSON.stringify(responseData), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      const response = await client.post('/test', requestData)

      expect(response.data).toEqual(responseData)
      expect(response.status).toBe(201)
    })

    it('should make PUT requests', async () => {
      const requestData = { id: 1, name: 'updated' }
      const mockResponse = new Response(JSON.stringify(requestData), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      const response = await client.put('/test/1', requestData)

      expect(response.data).toEqual(requestData)
    })

    it('should make DELETE requests', async () => {
      const mockResponse = new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      const response = await client.delete('/test/1')

      expect(response.data).toEqual({ success: true })
    })

    it('should handle query parameters', async () => {
      const mockResponse = new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockResponse)

      await client.get('/test', { page: 1, limit: 10 })

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('?page=1&limit=10'),
        expect.any(Object)
      )
    })

    it('should set custom headers', () => {
      client.setHeader('Authorization', 'Bearer token123')

      expect(client['headers']['Authorization']).toBe('Bearer token123')
    })

    it('should remove headers', () => {
      client.setHeader('X-Custom', 'value')
      client.removeHeader('X-Custom')

      expect(client['headers']['X-Custom']).toBeUndefined()
    })

    it('should handle timeout errors', async () => {
      // Create a timeout by rejecting with AbortError
      // We need to mock multiple times because of retries
      const abortError = new Error('Aborted')
      ;(abortError as any).name = 'AbortError'
      
      // Mock all retry attempts
      fetchMock.mockRejectedValue(abortError)

      await expect(client.get('/test')).rejects.toThrow('Request timeout')
    })

    it('should handle network errors', async () => {
      fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      await expect(client.get('/test')).rejects.toThrow('Network error')
    })

    it('should handle HTTP error responses', async () => {
      const mockResponse = new Response(
        JSON.stringify({ message: 'Not found', code: 'NOT_FOUND' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      )

      fetchMock.mockResolvedValueOnce(mockResponse)

      await expect(client.get('/test')).rejects.toThrow()
    })

    it('should retry on configured status codes', async () => {
      const mockErrorResponse = new Response(JSON.stringify({ error: 'Server error' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      })

      const mockSuccessResponse = new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })

      fetchMock.mockResolvedValueOnce(mockErrorResponse)
      fetchMock.mockResolvedValueOnce(mockSuccessResponse)

      const response = await client.get('/test')

      expect(response.data).toEqual({ success: true })
      expect(fetchMock).toHaveBeenCalledTimes(2)
    })
  })
})
