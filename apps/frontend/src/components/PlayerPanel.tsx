import { FormEvent, useState } from 'react'
import { Player, PrivatePlayerInfo, ResourceCard } from '../types'
import terraceImage from '../../images/terrace_logo.png'
import greatTerraceImage from '../../images/grand_terrace_logo.png'
import pathImage from '../../images/path_logo.png'

const RESOURCE_ICONS: Record<ResourceCard, string> = {
  gold: '🟡',
  stone: '🪨',
  cotton: '☁️',
  maize: '🌽',
  wood: '🪵',
}

interface PlayerPanelProps {
  players: Player[]
  turnOrder: string[]
  playerColors: Record<string, string>
  privateInfo: Record<string, PrivatePlayerInfo>
  privateErrors: Record<string, string>
  revealedPlayers: Set<string>
  onTokenSubmit: (nickname: string, token: string) => void
  onTokenClear: (nickname: string) => void
}

export default function PlayerPanel({
  players,
  turnOrder,
  playerColors,
  privateInfo,
  privateErrors,
  revealedPlayers,
  onTokenSubmit,
  onTokenClear,
}: PlayerPanelProps) {
  const activePlayer = turnOrder[0]

  if (players.length === 0) return null

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto">
      {players.map((player) => (
        <PlayerCard
          key={player.nickname}
          player={player}
          isActive={player.nickname === activePlayer}
          color={playerColors[player.nickname] || '#999'}
          privateInfo={privateInfo[player.nickname]}
          privateError={privateErrors[player.nickname]}
          revealed={revealedPlayers.has(player.nickname)}
          onTokenSubmit={onTokenSubmit}
          onTokenClear={onTokenClear}
        />
      ))}
    </div>
  )
}

interface PlayerCardProps {
  player: Player
  isActive: boolean
  color: string
  privateInfo?: PrivatePlayerInfo
  privateError?: string
  revealed: boolean
  onTokenSubmit: (nickname: string, token: string) => void
  onTokenClear: (nickname: string) => void
}

function PlayerCard({
  player,
  isActive,
  color,
  privateInfo: internal,
  privateError,
  revealed,
  onTokenSubmit,
  onTokenClear,
}: PlayerCardProps) {
  const nickname = player.nickname

  return (
    <div
      className={`rounded border-2 p-3 shadow ${
        isActive ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200 bg-white'
      }`}
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 rounded-full" style={{ backgroundColor: color }} />
          <span className={`font-semibold ${isActive ? 'text-yellow-700' : ''}`}>
            {nickname} {isActive && '(Active)'}
          </span>
        </div>
        <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-bold text-blue-800">
          {player.victory_points ?? 0} / 10 VP
        </span>
      </div>

      <div className="space-y-1 text-sm text-gray-700">
        <div className="flex justify-between">
          <span>Resources held:</span>
          <span className="rounded bg-amber-100 px-2 font-bold text-amber-800">
            {player.num_resources}
          </span>
        </div>
        {internal ? (
          <div className="grid grid-cols-2 gap-1 rounded bg-slate-50 p-2 text-xs">
            {(Object.keys(RESOURCE_ICONS) as ResourceCard[]).map((resource) => (
              <span key={resource} className="flex items-center justify-between gap-2">
                <span>
                  {RESOURCE_ICONS[resource]} {resource}
                </span>
                <strong>{internal.resources[resource] ?? 0}</strong>
              </span>
            ))}
          </div>
        ) : (
          <p className="rounded bg-slate-100 p-2 text-xs text-slate-500">
            🔒 Exact resource types are private.
          </p>
        )}
        <div className="flex justify-between">
          <span>Wisdom cards:</span>
          <span className="font-semibold">
            {player.num_hidden_wisdom_cards} hidden + {player.played_wisdom_cards.length} played
          </span>
        </div>

        {internal && internal.wisdom_cards.length > 0 && (
          <div className="mt-2 rounded bg-purple-50 p-2">
            <div className="text-xs font-semibold text-purple-800">Owned wisdom cards</div>
            <div className="mt-1 flex flex-wrap gap-1">
              {internal.wisdom_cards.map((card, idx) => (
                <span
                  key={`${card}-${idx}`}
                  className="rounded bg-purple-200 px-2 py-1 text-xs text-purple-900"
                >
                  {card}
                </span>
              ))}
            </div>
          </div>
        )}

        <PlayerTokenControl
          nickname={nickname}
          revealed={revealed}
          error={privateError}
          onSubmit={onTokenSubmit}
          onClear={onTokenClear}
        />

        <div className="mt-2 border-t border-gray-300 pt-2">
          <div className="mb-1 text-xs font-semibold text-gray-600">
            Pieces on board / available:
          </div>
          <div className="grid grid-cols-1 gap-1 text-xs">
            <span className="flex items-center gap-3">
              <img src={terraceImage} alt="" className="h-10 w-10 object-cover" />
              Terraces: {5 - player.available_terraces} / {player.available_terraces}
            </span>
            <span className="flex items-center gap-3">
              <img src={greatTerraceImage} alt="" className="h-12 w-12 object-cover" />
              Great terraces: {4 - player.available_great_terraces} /{' '}
              {player.available_great_terraces}
            </span>
            <span className="flex items-center gap-3">
              <img src={pathImage} alt="" className="h-10 w-10 object-contain" />
              Paths: {15 - player.available_paths} / {player.available_paths}
            </span>
          </div>
        </div>

        {player.played_wisdom_cards.length > 0 && (
          <div className="mt-2 border-t border-gray-300 pt-2">
            <div className="mb-1 text-xs font-semibold text-gray-600">Played Cards:</div>
            <div className="flex flex-wrap gap-1">
              {player.played_wisdom_cards.map((card, idx) => (
                <span key={idx} className="rounded bg-purple-100 px-2 py-1 text-xs text-purple-700">
                  {card}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

interface PlayerTokenControlProps {
  nickname: string
  revealed: boolean
  error?: string
  onSubmit: (nickname: string, token: string) => void
  onClear: (nickname: string) => void
}

function PlayerTokenControl({
  nickname,
  revealed,
  error,
  onSubmit,
  onClear,
}: PlayerTokenControlProps) {
  const [token, setToken] = useState('')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const trimmed = token.trim()
    if (!trimmed) return
    onSubmit(nickname, trimmed)
    setToken('')
  }

  if (revealed) {
    return (
      <div className="mt-2 rounded border border-emerald-200 bg-emerald-50 p-2 text-xs text-emerald-800">
        <div className="flex items-center justify-between gap-2">
          <span>
            {error ? '🔒 Token could not unlock this hand' : '🔓 Private hand authorized'}
          </span>
          <button
            type="button"
            onClick={() => onClear(nickname)}
            className="font-semibold underline"
          >
            Hide
          </button>
        </div>
        {error && <p className="mt-1 text-red-700">{error}</p>}
      </div>
    )
  }

  return (
    <form onSubmit={submit} className="mt-2 rounded border border-slate-200 bg-white p-2">
      <label className="block text-xs font-semibold text-slate-600" htmlFor={`token-${nickname}`}>
        Optional player token
      </label>
      <div className="mt-1 flex gap-1">
        <input
          id={`token-${nickname}`}
          type="password"
          value={token}
          onChange={(event) => setToken(event.target.value)}
          autoComplete="off"
          placeholder="Session token"
          className="min-w-0 flex-1 rounded border border-slate-300 px-2 py-1 text-xs"
        />
        <button
          type="submit"
          className="rounded bg-slate-800 px-2 py-1 text-xs font-semibold text-white"
        >
          Show
        </button>
      </div>
      {error && <p className="mt-1 text-xs text-red-700">{error}</p>}
    </form>
  )
}
