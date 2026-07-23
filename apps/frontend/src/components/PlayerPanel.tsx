import { FormEvent, useState } from 'react'
import { Player, PrivatePlayerInfo, ResourceCard } from '../types'

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
  currentPlayerIdx: number
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
  currentPlayerIdx,
  playerColors,
  privateInfo,
  privateErrors,
  revealedPlayers,
  onTokenSubmit,
  onTokenClear,
}: PlayerPanelProps) {
  const orderedNames = turnOrder.length > 0 ? turnOrder : players.map(player => player.nickname)

  return (
    <div className="bg-white rounded-lg shadow p-4 h-full overflow-y-auto">
      <h2 className="text-xl font-bold mb-4">Players</h2>

      <div className="space-y-3">
        {orderedNames.map((nickname, idx) => {
          const player = players.find(p => p.nickname === nickname)
          if (!player) return null

          const isActive = idx === currentPlayerIdx
          const color = playerColors[nickname] || '#999'
          const internal = privateInfo[nickname]

          return (
            <div
              key={nickname}
              className={`p-3 rounded border-2 ${
                isActive ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className={`font-semibold ${isActive ? 'text-yellow-700' : ''}`}>
                    {nickname} {isActive && '(Active)'}
                  </span>
                </div>
                <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-bold text-blue-800">{player.victory_points ?? 0} / 10 VP</span>
              </div>

              <div className="text-sm space-y-1 text-gray-700">
                <div className="flex justify-between">
                  <span>Resources held:</span>
                  <span className="rounded bg-amber-100 px-2 font-bold text-amber-800">{player.num_resources}</span>
                </div>
                {internal ? (
                  <div className="grid grid-cols-2 gap-1 rounded bg-slate-50 p-2 text-xs">
                    {(Object.keys(RESOURCE_ICONS) as ResourceCard[]).map(resource => (
                      <span key={resource} className="flex items-center justify-between gap-2">
                        <span>{RESOURCE_ICONS[resource]} {resource}</span>
                        <strong>{internal.resources[resource] ?? 0}</strong>
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="rounded bg-slate-100 p-2 text-xs text-slate-500">🔒 Exact resource types are private.</p>
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
                        <span key={`${card}-${idx}`} className="rounded bg-purple-200 px-2 py-1 text-xs text-purple-900">{card}</span>
                      ))}
                    </div>
                  </div>
                )}

                <PlayerTokenControl
                  nickname={nickname}
                  revealed={revealedPlayers.has(nickname)}
                  error={privateErrors[nickname]}
                  onSubmit={onTokenSubmit}
                  onClear={onTokenClear}
                />

                <div className="mt-2 pt-2 border-t border-gray-300">
                  <div className="text-xs font-semibold text-gray-600 mb-1">Pieces on board / available:</div>
                  <div className="grid grid-cols-1 gap-1 text-xs">
                    <span>🏠 Terraces: {5 - player.available_terraces} / {player.available_terraces}</span>
                    <span>🏛️ Great terraces: {4 - player.available_great_terraces} / {player.available_great_terraces}</span>
                    <span>🛤️ Paths: {15 - player.available_paths} / {player.available_paths}</span>
                  </div>
                </div>

                {player.played_wisdom_cards.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-300">
                    <div className="text-xs font-semibold text-gray-600 mb-1">Played Cards:</div>
                    <div className="flex flex-wrap gap-1">
                      {player.played_wisdom_cards.map((card, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded"
                        >
                          {card}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
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

function PlayerTokenControl({ nickname, revealed, error, onSubmit, onClear }: PlayerTokenControlProps) {
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
          <span>{error ? '🔒 Token could not unlock this hand' : '🔓 Private hand authorized'}</span>
          <button type="button" onClick={() => onClear(nickname)} className="font-semibold underline">Hide</button>
        </div>
        {error && <p className="mt-1 text-red-700">{error}</p>}
      </div>
    )
  }

  return (
    <form onSubmit={submit} className="mt-2 rounded border border-slate-200 bg-white p-2">
      <label className="block text-xs font-semibold text-slate-600" htmlFor={`token-${nickname}`}>Optional player token</label>
      <div className="mt-1 flex gap-1">
        <input
          id={`token-${nickname}`}
          type="password"
          value={token}
          onChange={event => setToken(event.target.value)}
          autoComplete="off"
          placeholder="Session token"
          className="min-w-0 flex-1 rounded border border-slate-300 px-2 py-1 text-xs"
        />
        <button type="submit" className="rounded bg-slate-800 px-2 py-1 text-xs font-semibold text-white">Show</button>
      </div>
      {error && <p className="mt-1 text-xs text-red-700">{error}</p>}
    </form>
  )
}
