import { describe, expect, it } from 'vitest'

import { hexToPixel, getHexVertices } from './hexUtils'

describe('hexToPixel', () => {
  it('maps the origin hex to the origin pixel', () => {
    expect(hexToPixel(0, 0)).toEqual({ x: 0, y: 0 })
  })
})

describe('getHexVertices', () => {
  it('returns six vertices for a hex', () => {
    expect(getHexVertices(0, 0)).toHaveLength(6)
  })
})
