import { Hex, PlayedSettlement, PlayedStonePath, HEX_TYPE_COLORS } from '../types'
import { hexToPixel, getHexVertices, getHexVertexCoord, getHexEdges } from '../hexUtils'

interface Harbour {
  resource: string | null
  vertices: [[number, number, number], [number, number, number]]
}

// These are the canonical harbour vertices enforced by the backend.
const HARBOURS: Harbour[] = [
  { resource: 'wood', vertices: [[-1, -1, 4], [-1, -1, 5]] },
  { resource: null, vertices: [[0, -2, 0], [0, -2, 5]] },
  { resource: 'maize', vertices: [[1, -2, 0], [1, -2, 1]] },
  { resource: 'stone', vertices: [[2, -1, 0], [2, -1, 1]] },
  { resource: null, vertices: [[2, 0, 1], [2, 0, 2]] },
  { resource: 'cotton', vertices: [[1, 1, 2], [1, 1, 3]] },
  { resource: null, vertices: [[-1, 2, 2], [-1, 2, 3]] },
  { resource: null, vertices: [[-2, 2, 3], [-2, 2, 4]] },
  { resource: 'gold', vertices: [[-2, 1, 4], [-2, 1, 5]] },
]

interface Point {
  x: number
  y: number
}

const BOARD_CENTER = { offsetX: 450, offsetY: 400 }

function convexHull(points: Point[]): Point[] {
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y)
  const cross = (origin: Point, a: Point, b: Point) =>
    (a.x - origin.x) * (b.y - origin.y) - (a.y - origin.y) * (b.x - origin.x)
  const half = (source: Point[]) => {
    const result: Point[] = []
    source.forEach(point => {
      while (result.length >= 2 && cross(result[result.length - 2], result[result.length - 1], point) <= 0) result.pop()
      result.push(point)
    })
    return result
  }
  const lower = half(sorted)
  const upper = half([...sorted].reverse())
  return [...lower.slice(0, -1), ...upper.slice(0, -1)]
}

function polygonPoints(points: Point[], scale = 1): string {
  return points
    .map(point => `${point.x * scale + BOARD_CENTER.offsetX},${point.y * scale + BOARD_CENTER.offsetY}`)
    .join(' ')
}

function regularHexagon(radius: number): Point[] {
  return Array.from({ length: 6 }, (_, index) => {
    const angle = -Math.PI / 2 + index * Math.PI / 3
    return { x: radius * Math.cos(angle), y: radius * Math.sin(angle) }
  })
}

interface GameBoardProps {
  hexes: Hex[]
  settlements: PlayedSettlement[]
  paths: PlayedStonePath[]
  conquistadorLocation: { q: number; r: number }
  playerColors: Record<string, string>
  onHexClick?: (hex: Hex) => void
  onVertexClick?: (q: number, r: number, direction: number) => void
  onEdgeClick?: (q: number, r: number, direction: number) => void
}

export default function GameBoard({
  hexes,
  settlements,
  paths,
  conquistadorLocation,
  playerColors,
  onHexClick,
  onVertexClick,
  onEdgeClick,
}: GameBoardProps) {
  const offset = BOARD_CENTER
  const terrainHull = convexHull(
    hexes.flatMap(hex =>
      getHexVertices(hex.coordinate.q, hex.coordinate.r).map(([x, y]) => ({ x, y })),
    ),
  )

  const settlementsByLocation = new Map<string, PlayedSettlement>()
  settlements.forEach(s => {
    const key = `${s.location.hex_coord.q},${s.location.hex_coord.r},${s.location.direction}`
    settlementsByLocation.set(key, s)
  })

  const pathsByLocation = new Map<string, PlayedStonePath>()
  paths.forEach(p => {
    const key = `${p.location.hex_coord.q},${p.location.hex_coord.r},${p.location.direction}`
    pathsByLocation.set(key, p)
  })

  return (
    <div className="overflow-hidden rounded-lg bg-sky-950">
      <svg
        viewBox="0 0 900 800"
        className="block h-auto w-full bg-sky-950"
        role="img"
        aria-label="Teyuna board surrounded by water, sand, and trading harbors"
      >
        <polygon points={polygonPoints(regularHexagon(385))} fill="#0e7490" stroke="#164e63" strokeWidth="8" />
        <polygon points={polygonPoints(terrainHull, 1.12)} fill="#d9b77e" />
        <polygon
          points={polygonPoints(terrainHull, 1.01)}
          fill="none"
          stroke="#d9b77e"
          strokeWidth="14"
          strokeLinejoin="round"
          pointerEvents="none"
        />

        {hexes.map(hex => {
          const vertices = getHexVertices(hex.coordinate.q, hex.coordinate.r)
          const points = vertices.map(v => `${v[0] + offset.offsetX},${v[1] + offset.offsetY}`).join(' ')
          const color = HEX_TYPE_COLORS[hex.type]

          return (
            <g key={`hex-${hex.coordinate.q}-${hex.coordinate.r}`}>
              <polygon
                points={points}
                fill={color}
                stroke="#333"
                strokeWidth="2"
                opacity="0.8"
                onClick={() => onHexClick?.(hex)}
                className="cursor-pointer hover:opacity-100"
              />

              {hex.number && (
                <text
                  x={hexToPixel(hex.coordinate.q, hex.coordinate.r).x + offset.offsetX}
                  y={hexToPixel(hex.coordinate.q, hex.coordinate.r).y + offset.offsetY + 5}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="font-bold text-lg"
                  fill="#000"
                >
                  {hex.number}
                </text>
              )}

              <text
                x={hexToPixel(hex.coordinate.q, hex.coordinate.r).x + offset.offsetX}
                y={hexToPixel(hex.coordinate.q, hex.coordinate.r).y + offset.offsetY - 20}
                textAnchor="middle"
                className="text-xs"
                fill="#666"
              >
                {hex.type}
              </text>
            </g>
          )
        })}

        {HARBOURS.map(harbour => {
          const [first, second] = harbour.vertices.map(([q, r, direction]) =>
            getHexVertexCoord(q, r, direction),
          )
          const middle = { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 }
          const distance = Math.hypot(middle.x, middle.y) || 1
          const label = harbour.resource ? `⛵ 2:1 ${harbour.resource}` : '⛵ 3:1 any'
          const labelX = middle.x + (middle.x / distance) * 78 + offset.offsetX
          const labelY = middle.y + (middle.y / distance) * 78 + offset.offsetY
          return (
            <g key={`harbour-${harbour.vertices[0].join('-')}`}>
              <line
                x1={middle.x + offset.offsetX}
                y1={middle.y + offset.offsetY}
                x2={labelX}
                y2={labelY}
                stroke="#ecfeff"
                strokeWidth="2"
                strokeDasharray="5 4"
                strokeLinecap="round"
              />
              <circle cx={first.x + offset.offsetX} cy={first.y + offset.offsetY} r="4" fill="#fef3c7" stroke="#92400e" />
              <circle cx={second.x + offset.offsetX} cy={second.y + offset.offsetY} r="4" fill="#fef3c7" stroke="#92400e" />
              <rect x={labelX - 52} y={labelY - 14} width="104" height="28" rx="14" fill="#ecfeff" stroke="#155e75" strokeWidth="2" />
              <text x={labelX} y={labelY + 4} textAnchor="middle" className="text-[11px] font-bold" fill="#164e63">
                {label}
              </text>
            </g>
          )
        })}

        {hexes.map(hex => {
          const edges = getHexEdges(hex.coordinate.q, hex.coordinate.r)
          return edges.map(edge => {
            const key = `${hex.coordinate.q},${hex.coordinate.r},${edge.direction}`
            const path = pathsByLocation.get(key)

            return (
              <g key={`edge-${key}`}>
                {path && (
                  <line
                    x1={getHexVertices(hex.coordinate.q, hex.coordinate.r)[edge.direction][0] + offset.offsetX}
                    y1={getHexVertices(hex.coordinate.q, hex.coordinate.r)[edge.direction][1] + offset.offsetY}
                    x2={getHexVertices(hex.coordinate.q, hex.coordinate.r)[(edge.direction + 1) % 6][0] + offset.offsetX}
                    y2={getHexVertices(hex.coordinate.q, hex.coordinate.r)[(edge.direction + 1) % 6][1] + offset.offsetY}
                    stroke={playerColors[path.owner] || '#999'}
                    strokeWidth="8"
                    strokeLinecap="round"
                  />
                )}
                {!path && (
                  <circle
                    cx={edge.x + offset.offsetX}
                    cy={edge.y + offset.offsetY}
                    r="5"
                    fill="none"
                    stroke="#ccc"
                    strokeWidth="1"
                    opacity="0.3"
                    onClick={() => onEdgeClick?.(hex.coordinate.q, hex.coordinate.r, edge.direction)}
                    className="cursor-pointer hover:opacity-100"
                  />
                )}
              </g>
            )
          })
        })}

        {hexes.map(hex => {
          const vertices = getHexVertices(hex.coordinate.q, hex.coordinate.r)
          return vertices.map((_, direction) => {
            const key = `${hex.coordinate.q},${hex.coordinate.r},${direction}`
            const settlement = settlementsByLocation.get(key)
            const vertex = getHexVertexCoord(hex.coordinate.q, hex.coordinate.r, direction)

            return (
              <g key={`vertex-${key}`}>
                {settlement && (
                  <circle
                    cx={vertex.x + offset.offsetX}
                    cy={vertex.y + offset.offsetY}
                    r={settlement.type === 'great terrace' ? 10 : 7}
                    fill={playerColors[settlement.owner] || '#999'}
                    stroke="#000"
                    strokeWidth="2"
                    onClick={() => onVertexClick?.(hex.coordinate.q, hex.coordinate.r, direction)}
                    className="cursor-pointer"
                  />
                )}
                {!settlement && (
                  <circle
                    cx={vertex.x + offset.offsetX}
                    cy={vertex.y + offset.offsetY}
                    r="4"
                    fill="none"
                    stroke="#ccc"
                    strokeWidth="1"
                    opacity="0.3"
                    onClick={() => onVertexClick?.(hex.coordinate.q, hex.coordinate.r, direction)}
                    className="cursor-pointer hover:opacity-100"
                  />
                )}
              </g>
            )
          })
        })}

        {hexes.map(hex => {
          if (hex.coordinate.q === conquistadorLocation.q && hex.coordinate.r === conquistadorLocation.r) {
            const { x, y } = hexToPixel(hex.coordinate.q, hex.coordinate.r)
            return (
              <g key="conquistador">
                <circle
                  cx={x + offset.offsetX}
                  cy={y + offset.offsetY}
                  r="8"
                  fill="none"
                  stroke="#FF6B6B"
                  strokeWidth="3"
                />
                <text
                  x={x + offset.offsetX}
                  y={y + offset.offsetY}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="font-bold"
                  fill="#FF6B6B"
                >
                  C
                </text>
              </g>
            )
          }
          return null
        })}
      </svg>
      <div className="flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-200 bg-white px-4 py-3 text-xs text-slate-600">
        <strong className="text-slate-800">Harbors:</strong>
        <span><b>3:1 any</b> — give three identical resources for one resource</span>
        <span><b>2:1 resource</b> — give two of the named resource for one resource</span>
      </div>
    </div>
  )
}
