import { describe, expect, it } from 'vitest'

import { getHexEdges, getHexVertexCoord, hexToPixel, getHexVertices } from './hexUtils'

describe('hexToPixel', () => {
  it('maps the origin hex to the origin pixel', () => {
    expect(hexToPixel(0, 0)).toEqual({ x: 0, y: 0 })
  })

  it('places the (1, 0) neighbour due east, as pointy-top requires', () => {
    const neighbour = hexToPixel(1, 0)
    expect(neighbour.x).toBeCloseTo(60 * Math.sqrt(3))
    expect(neighbour.y).toBeCloseTo(0)
  })
})

describe('getHexVertices', () => {
  it('returns six vertices for a hex', () => {
    expect(getHexVertices(0, 0)).toHaveLength(6)
  })
})

describe('backend canonical directions', () => {
  it('maps direction zero to the top vertex', () => {
    const vertex = getHexVertexCoord(0, 0, 0)
    expect(vertex.x).toBeCloseTo(0)
    expect(vertex.y).toBeCloseTo(-60)
  })

  it('renders canonical aliases at the same physical vertex', () => {
    const canonical = getHexVertexCoord(0, 0, 0)
    const firstAlias = getHexVertexCoord(1, -1, 4)
    const secondAlias = getHexVertexCoord(0, -1, 2)

    expect(firstAlias.x).toBeCloseTo(canonical.x)
    expect(firstAlias.y).toBeCloseTo(canonical.y)
    expect(secondAlias.x).toBeCloseTo(canonical.x)
    expect(secondAlias.y).toBeCloseTo(canonical.y)
  })

  it('maps canonical edge zero to the upper-right side', () => {
    const edge = getHexEdges(0, 0)[0]
    expect(edge.direction).toBe(0)
    expect(edge.x1).toBeCloseTo(0)
    expect(edge.y1).toBeCloseTo(-60)
    expect(edge.x2).toBeCloseTo(30 * Math.sqrt(3))
    expect(edge.y2).toBeCloseTo(-30)
  })
})
