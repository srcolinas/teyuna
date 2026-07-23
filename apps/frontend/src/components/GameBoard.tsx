import { useState } from 'react'
import {
  Harbour,
  Hex,
  HexCoordinate,
  PlayedSettlement,
  PlayedStonePath,
  HEX_TYPE_COLORS,
} from '../types'
import { hexToPixel, getHexVertices, getHexVertexCoord, getHexEdges } from '../hexUtils'
import terraceRed from '../../images/terrace_red.png'
import terraceBlue from '../../images/terrace_blue.png'
import terraceYellow from '../../images/terrace_yellow.png'
import terracePurple from '../../images/terrace_purple.png'
import terraceGreen from '../../images/terrace_green.png'
import grandTerraceRed from '../../images/grand_terrace_red.png'
import grandTerraceBlue from '../../images/grand_terrace_blue.png'
import grandTerraceYellow from '../../images/grand_terrace_yellow.png'
import grandTerracePurple from '../../images/grand_terrace_purple.png'
import grandTerraceGreen from '../../images/grand_terrace_green.png'

interface Point {
  x: number
  y: number
}

const BOARD_CENTER = { offsetX: 450, offsetY: 400 }
const TERRACE_IMAGES: Record<string, string> = {
  '#ef4444': terraceRed,
  '#2563eb': terraceBlue,
  '#eab308': terraceYellow,
  '#7c3aed': terracePurple,
  '#16a34a': terraceGreen,
}
const GREAT_TERRACE_IMAGES: Record<string, string> = {
  '#ef4444': grandTerraceRed,
  '#2563eb': grandTerraceBlue,
  '#eab308': grandTerraceYellow,
  '#7c3aed': grandTerracePurple,
  '#16a34a': grandTerraceGreen,
}

function convexHull(points: Point[]): Point[] {
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y)
  const cross = (origin: Point, a: Point, b: Point) =>
    (a.x - origin.x) * (b.y - origin.y) - (a.y - origin.y) * (b.x - origin.x)
  const half = (source: Point[]) => {
    const result: Point[] = []
    source.forEach((point) => {
      while (
        result.length >= 2 &&
        cross(result[result.length - 2], result[result.length - 1], point) <= 0
      )
        result.pop()
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
    .map(
      (point) =>
        `${point.x * scale + BOARD_CENTER.offsetX},${point.y * scale + BOARD_CENTER.offsetY}`,
    )
    .join(' ')
}

function regularHexagon(radius: number): Point[] {
  return Array.from({ length: 6 }, (_, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI) / 3
    return { x: radius * Math.cos(angle), y: radius * Math.sin(angle) }
  })
}

function sameHex(a: HexCoordinate | null, b: HexCoordinate): boolean {
  return a !== null && a.q === b.q && a.r === b.r
}

interface GameBoardProps {
  hexes: Hex[]
  harbours: Harbour[]
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
  harbours,
  settlements,
  paths,
  conquistadorLocation,
  playerColors,
  onHexClick,
  onVertexClick,
  onEdgeClick,
}: GameBoardProps) {
  const [hoveredHex, setHoveredHex] = useState<HexCoordinate | null>(null)
  const offset = BOARD_CENTER
  const terrainHull = convexHull(
    hexes.flatMap((hex) =>
      getHexVertices(hex.coordinate.q, hex.coordinate.r).map(([x, y]) => ({ x, y })),
    ),
  )

  const settlementsByLocation = new Map<string, PlayedSettlement>()
  settlements.forEach((s) => {
    const key = `${s.location.hex_coord.q},${s.location.hex_coord.r},${s.location.direction}`
    settlementsByLocation.set(key, s)
  })

  const pathsByLocation = new Map<string, PlayedStonePath>()
  paths.forEach((p) => {
    const key = `${p.location.hex_coord.q},${p.location.hex_coord.r},${p.location.direction}`
    pathsByLocation.set(key, p)
  })

  return (
    <div className="overflow-hidden rounded-lg bg-[#293681]">
      <svg
        viewBox="0 0 900 800"
        className="block h-auto w-full bg-[#293681]"
        role="img"
        aria-label="Teyuna board surrounded by water, sand, and trading harbors"
      >
        <polygon
          points={polygonPoints(regularHexagon(385))}
          fill="#017DD5"
          stroke="#164e63"
          strokeWidth="8"
        />
        <polygon points={polygonPoints(terrainHull, 1.12)} fill="#EED5A0" />
        <polygon
          points={polygonPoints(terrainHull, 1.01)}
          fill="none"
          stroke="#EED5A0"
          strokeWidth="14"
          strokeLinejoin="round"
          pointerEvents="none"
        />

        {hexes.map((hex) => {
          const vertices = getHexVertices(hex.coordinate.q, hex.coordinate.r)
          const points = vertices
            .map((v) => `${v[0] + offset.offsetX},${v[1] + offset.offsetY}`)
            .join(' ')
          const color = HEX_TYPE_COLORS[hex.type]
          const center = hexToPixel(hex.coordinate.q, hex.coordinate.r)
          const isHovered = sameHex(hoveredHex, hex.coordinate)

          return (
            <g key={`hex-${hex.coordinate.q}-${hex.coordinate.r}`}>
              <polygon
                points={points}
                fill={color}
                stroke="#333"
                strokeWidth="2"
                opacity={isHovered ? 1 : 0.8}
                onClick={() => onHexClick?.(hex)}
                onMouseEnter={() => setHoveredHex(hex.coordinate)}
                onMouseLeave={() => setHoveredHex(null)}
                className="cursor-pointer"
              />

              {hex.number && hex.type !== 'desert' && (
                <g className="pointer-events-none">
                  <circle
                    cx={center.x + offset.offsetX}
                    cy={center.y + offset.offsetY + 4}
                    r="15"
                    fill="#fff"
                    stroke="#e2e8f0"
                    strokeWidth="1.5"
                  />
                  <text
                    x={center.x + offset.offsetX}
                    y={center.y + offset.offsetY + 5}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    className="font-bold text-lg"
                    fill={hex.number === 6 || hex.number === 8 ? '#dc2626' : '#000'}
                  >
                    {hex.number}
                  </text>
                </g>
              )}

              <text
                x={center.x + offset.offsetX}
                y={center.y + offset.offsetY - 20}
                textAnchor="middle"
                className="pointer-events-none text-sm font-semibold"
                fill="#fff"
              >
                {hex.type.charAt(0).toUpperCase() + hex.type.slice(1)}
              </text>

              {isHovered && (
                <text
                  x={center.x + offset.offsetX}
                  y={center.y + offset.offsetY + 28}
                  textAnchor="middle"
                  className="pointer-events-none text-xs font-bold"
                  fill="#0f172a"
                >
                  ({hex.coordinate.q}, {hex.coordinate.r})
                </text>
              )}
            </g>
          )
        })}

        {harbours.map((harbour) => {
          const [firstVertex, secondVertex] = harbour.vertices
          const first = getHexVertexCoord(
            firstVertex.hex_coord.q,
            firstVertex.hex_coord.r,
            firstVertex.direction,
          )
          const second = getHexVertexCoord(
            secondVertex.hex_coord.q,
            secondVertex.hex_coord.r,
            secondVertex.direction,
          )
          const middle = { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 }
          const distance = Math.hypot(middle.x, middle.y) || 1
          const label = harbour.resource ? `⛵ 2:1 ${harbour.resource}` : '⛵ 3:1 any'
          const labelDistance = 112
          const labelX = middle.x + (middle.x / distance) * labelDistance + offset.offsetX
          const labelY = middle.y + (middle.y / distance) * labelDistance + offset.offsetY
          const harbourKey = [
            firstVertex.hex_coord.q,
            firstVertex.hex_coord.r,
            firstVertex.direction,
            secondVertex.hex_coord.q,
            secondVertex.hex_coord.r,
            secondVertex.direction,
          ].join('-')
          return (
            <g key={`harbour-${harbourKey}`}>
              <line
                x1={labelX}
                y1={labelY}
                x2={first.x + offset.offsetX}
                y2={first.y + offset.offsetY}
                stroke="#ecfeff"
                strokeWidth="2"
                strokeDasharray="5 4"
                strokeLinecap="round"
              />
              <line
                x1={labelX}
                y1={labelY}
                x2={second.x + offset.offsetX}
                y2={second.y + offset.offsetY}
                stroke="#ecfeff"
                strokeWidth="2"
                strokeDasharray="5 4"
                strokeLinecap="round"
              />
              <circle
                cx={first.x + offset.offsetX}
                cy={first.y + offset.offsetY}
                r="4"
                fill="#fef3c7"
                stroke="#92400e"
              />
              <circle
                cx={second.x + offset.offsetX}
                cy={second.y + offset.offsetY}
                r="4"
                fill="#fef3c7"
                stroke="#92400e"
              />
              <rect
                x={labelX - 52}
                y={labelY - 14}
                width="104"
                height="28"
                rx="14"
                fill="#ecfeff"
                stroke="#155e75"
                strokeWidth="2"
              />
              <text
                x={labelX}
                y={labelY + 4}
                textAnchor="middle"
                className="text-[11px] font-bold"
                fill="#164e63"
              >
                {label}
              </text>
            </g>
          )
        })}

        {hexes.map((hex) => {
          const edges = getHexEdges(hex.coordinate.q, hex.coordinate.r)
          return edges.map((edge) => {
            const key = `${hex.coordinate.q},${hex.coordinate.r},${edge.direction}`
            const path = pathsByLocation.get(key)

            return (
              <g key={`edge-${key}`}>
                {path && (
                  <line
                    x1={edge.x1 + offset.offsetX}
                    y1={edge.y1 + offset.offsetY}
                    x2={edge.x2 + offset.offsetX}
                    y2={edge.y2 + offset.offsetY}
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
                    onClick={() =>
                      onEdgeClick?.(hex.coordinate.q, hex.coordinate.r, edge.direction)
                    }
                    className="cursor-pointer hover:opacity-100"
                  />
                )}
              </g>
            )
          })
        })}

        {hexes.map((hex) => {
          const vertices = getHexVertices(hex.coordinate.q, hex.coordinate.r)
          return vertices.map((_, direction) => {
            const key = `${hex.coordinate.q},${hex.coordinate.r},${direction}`
            const settlement = settlementsByLocation.get(key)
            const vertex = getHexVertexCoord(hex.coordinate.q, hex.coordinate.r, direction)
            const isGreatTerrace = settlement?.type === 'great terrace'
            const circleRadius = isGreatTerrace ? 27 : 22
            const pieceSize = isGreatTerrace ? 42 : 34
            const pieceRadius = pieceSize / 2
            const ownerColor = settlement ? playerColors[settlement.owner] || '#ef4444' : '#ef4444'
            const pieceImage = isGreatTerrace
              ? GREAT_TERRACE_IMAGES[ownerColor] || grandTerraceRed
              : TERRACE_IMAGES[ownerColor] || terraceRed

            return (
              <g key={`vertex-${key}`}>
                {settlement && (
                  <g
                    onClick={() => onVertexClick?.(hex.coordinate.q, hex.coordinate.r, direction)}
                    className="cursor-pointer"
                  >
                    <circle
                      cx={vertex.x + offset.offsetX}
                      cy={vertex.y + offset.offsetY}
                      r={circleRadius}
                      fill="#fff"
                      stroke={ownerColor}
                      strokeWidth="4"
                    />
                    <image
                      href={pieceImage}
                      x={vertex.x + offset.offsetX - pieceRadius}
                      y={vertex.y + offset.offsetY - pieceRadius}
                      width={pieceSize}
                      height={pieceSize}
                      preserveAspectRatio="xMidYMid slice"
                    />
                  </g>
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

        {hexes.map((hex) => {
          if (
            hex.coordinate.q === conquistadorLocation.q &&
            hex.coordinate.r === conquistadorLocation.r
          ) {
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
        <span>
          <b>3:1 any</b> — give three identical resources for one resource
        </span>
        <span>
          <b>2:1 resource</b> — give two of the named resource for one resource
        </span>
      </div>
    </div>
  )
}
