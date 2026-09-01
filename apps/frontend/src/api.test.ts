import { AxiosError, AxiosHeaders } from 'axios'
import { describe, expect, it } from 'vitest'

import { isNotFoundError } from './api'

function axiosErrorWithStatus(status: number): AxiosError {
  const config = { headers: new AxiosHeaders() }
  return new AxiosError('request failed', 'ERR_BAD_REQUEST', config, null, {
    status,
    statusText: '',
    data: {},
    headers: {},
    config,
  })
}

describe('isNotFoundError', () => {
  it('detects a missing game', () => {
    expect(isNotFoundError(axiosErrorWithStatus(404))).toBe(true)
  })

  it('ignores other error statuses', () => {
    expect(isNotFoundError(axiosErrorWithStatus(400))).toBe(false)
    expect(isNotFoundError(axiosErrorWithStatus(500))).toBe(false)
  })

  it('ignores network errors without a response', () => {
    expect(isNotFoundError(new AxiosError('Network Error'))).toBe(false)
  })

  it('ignores non-axios errors', () => {
    expect(isNotFoundError(new Error('boom'))).toBe(false)
  })
})
