import { Hex } from './types'

const HEX_SIZE = 60

export function hexToPixel(q: number, r: number): { x: number; y: number } {
  const x = HEX_SIZE * Math.sqrt(3) * (q + r / 2)
  const y = HEX_SIZE * (3 / 2) * r
  return { x, y }
}

/** Corners of a pointy-top hex, index 0 at the top corner then clockwise. */
export function getHexVertices(q: number, r: number): Array<[number, number]> {
  const { x, y } = hexToPixel(q, r)
  const vertices: Array<[number, number]> = []

  for (let i = 0; i < 6; i++) {
    const angle = -Math.PI / 2 + (Math.PI / 3) * i
    const px = x + HEX_SIZE * Math.cos(angle)
    const py = y + HEX_SIZE * Math.sin(angle)
    vertices.push([px, py])
  }

  return vertices
}

export function getHexCenter(q: number, r: number): { x: number; y: number } {
  return hexToPixel(q, r)
}

export function getHexEdges(
  q: number,
  r: number,
): Array<{
  x: number
  y: number
  x1: number
  y1: number
  x2: number
  y2: number
  direction: number
}> {
  const vertices = getHexVertices(q, r)
  const edges = []

  for (let direction = 0; direction < 6; direction++) {
    const v1 = vertices[direction]
    const v2 = vertices[(direction + 1) % 6]
    edges.push({
      x: (v1[0] + v2[0]) / 2,
      y: (v1[1] + v2[1]) / 2,
      x1: v1[0],
      y1: v1[1],
      x2: v2[0],
      y2: v2[1],
      direction,
    })
  }

  return edges
}

export function getHexVertexCoord(
  q: number,
  r: number,
  direction: number,
): { x: number; y: number } {
  const vertices = getHexVertices(q, r)
  return { x: vertices[direction][0], y: vertices[direction][1] }
}

export function getBoardOffset(hexes: Hex[]): { offsetX: number; offsetY: number } {
  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity

  hexes.forEach((hex) => {
    const { x, y } = hexToPixel(hex.coordinate.q, hex.coordinate.r)
    minX = Math.min(minX, x)
    maxX = Math.max(maxX, x)
    minY = Math.min(minY, y)
    maxY = Math.max(maxY, y)
  })

  return {
    offsetX: -minX + HEX_SIZE,
    offsetY: -minY + HEX_SIZE,
  }
}
