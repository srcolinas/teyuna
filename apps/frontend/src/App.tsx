import { useEffect, useMemo, useState } from 'react'
import { ActiveGame, PrivatePlayerInfo } from './types'
import { apiClient, apiErrorMessage, isNotFoundError } from './api'
import GameBoard from './components/GameBoard'
import PlayerPanel from './components/PlayerPanel'
import EventFeed, { GameEvent } from './components/EventFeed'
import teyunaLogo from '../images/teyuna_logo.png'

function App() {
  const gameId = new URLSearchParams(window.location.search).get('gameId')
  const [game, setGame] = useState<ActiveGame | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [events, setEvents] = useState<GameEvent[]>([])
  const [eventConnection, setEventConnection] = useState<'connecting' | 'live' | 'waiting'>(
    'connecting',
  )
  const [playerTokens, setPlayerTokens] = useState<Record<string, string>>({})
  const [privatePlayerInfo, setPrivatePlayerInfo] = useState<Record<string, PrivatePlayerInfo>>({})
  const [privateErrors, setPrivateErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!gameId) {
      setLoading(false)
      return
    }
    // A missing game never comes back: the server keeps games in memory only.
    if (notFound) return

    const fetchGame = async () => {
      try {
        setGame(await apiClient.getGame(gameId))
        setError(null)
      } catch (err) {
        if (isNotFoundError(err)) {
          setNotFound(true)
          return
        }
        setError(`Failed to load game: ${apiErrorMessage(err)}`)
      } finally {
        setLoading(false)
      }
    }

    void fetchGame()
    const interval = window.setInterval(fetchGame, 2000)
    return () => window.clearInterval(interval)
  }, [gameId, notFound])

  useEffect(() => {
    if (!gameId || notFound) return
    const entries = Object.entries(playerTokens)
    if (entries.length === 0) return

    const fetchPrivateInfo = async () => {
      await Promise.all(
        entries.map(async ([nickname, token]) => {
          try {
            const info = await apiClient.getPrivatePlayerInfo(gameId, token)
            setPrivatePlayerInfo((current) => ({ ...current, [nickname]: info }))
            setPrivateErrors((current) => {
              const next = { ...current }
              delete next[nickname]
              return next
            })
          } catch (err) {
            setPrivatePlayerInfo((current) => {
              const next = { ...current }
              delete next[nickname]
              return next
            })
            setPrivateErrors((current) => ({ ...current, [nickname]: apiErrorMessage(err) }))
          }
        }),
      )
    }

    void fetchPrivateInfo()
    const interval = window.setInterval(fetchPrivateInfo, 2000)
    return () => window.clearInterval(interval)
  }, [gameId, notFound, playerTokens])

  useEffect(() => {
    if (!gameId || notFound) return
    const source = new EventSource(`/games/${gameId}/events`)
    const eventNames = [
      'message',
      'failed_action',
      'successful_action',
      'phase_changed',
      'turn_changed',
      'biggest_army_changed',
      'longest_road_changed',
      'end_game',
    ] as const

    const handleEvent = (event: MessageEvent<string>) => {
      if (!event.lastEventId) return
      try {
        const data = JSON.parse(event.data) as Record<string, unknown>
        setEvents((current) => [
          ...current.slice(-99),
          { id: event.lastEventId, data, receivedAt: new Date() },
        ])
      } catch {
        // Drop malformed SSE payloads rather than inventing event shapes.
      }
    }

    source.onopen = () => setEventConnection('live')
    source.onerror = () => setEventConnection('waiting')
    for (const name of eventNames) {
      source.addEventListener(name, handleEvent)
    }
    return () => {
      for (const name of eventNames) {
        source.removeEventListener(name, handleEvent)
      }
      source.close()
    }
  }, [gameId, notFound])

  const playerColors = useMemo(() => {
    if (!game) return {}
    const palette = ['#ef4444', '#2563eb', '#eab308', '#7c3aed', '#16a34a']
    return Object.fromEntries(
      game.players.map((player, index) => [player.nickname, palette[index % palette.length]]),
    )
  }, [game])

  const submitPlayerToken = (nickname: string, token: string) => {
    setPlayerTokens((current) => ({ ...current, [nickname]: token }))
    setPrivateErrors((current) => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
  }

  const clearPlayerToken = (nickname: string) => {
    setPlayerTokens((current) => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
    setPrivatePlayerInfo((current) => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
    setPrivateErrors((current) => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
  }

  if (!gameId) return <GameFinder />

  if (notFound) return <GameNotFound gameId={gameId} />

  if (loading && !game) {
    return (
      <div className="min-h-screen grid place-items-center bg-slate-100 text-lg">
        Loading simulation…
      </div>
    )
  }

  if (!game) {
    return (
      <div className="min-h-screen grid place-items-center bg-slate-100">
        <div className="rounded-xl bg-white p-8 shadow">
          <h1 className="text-xl font-bold text-red-600">Simulation unavailable</h1>
          <p className="mt-2 text-slate-600">{error}</p>
        </div>
      </div>
    )
  }

  const activePlayer = game.turn_order[0]
  const nextPlayer = game.turn_order[1]
  const leftPlayers = game.players.slice(0, 2)
  const rightPlayers = game.players.slice(2)
  const winner =
    game.phase === 'end game'
      ? [...game.players].sort((left, right) => right.victory_points - left.victory_points)[0]
      : null
  const panelProps = {
    turnOrder: game.turn_order,
    playerColors,
    privateInfo: privatePlayerInfo,
    privateErrors,
    revealedPlayers: new Set(Object.keys(playerTokens)),
    onTokenSubmit: submitPlayerToken,
    onTokenClear: clearPlayerToken,
  }

  return (
    <main className="min-h-screen bg-white p-4 pb-24">
      <div className="mx-auto max-w-[90rem]">
        <header className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-emerald-700">
              Live agent simulation
            </p>
            <h1 className="flex items-center gap-3 text-3xl font-bold text-slate-900">
              Teyuna — The Lost City
              <img src={teyunaLogo} alt="Teyuna logo" className="h-12 w-12 object-contain" />
            </h1>
          </div>
          <div className="rounded-lg bg-white px-4 py-2 text-right shadow-sm">
            <p className="text-xs uppercase text-slate-500">Current phase</p>
            <p className="font-bold text-blue-700">{game.phase.toUpperCase()}</p>
            <p className="text-sm text-slate-600">
              {activePlayer ? `Active agent: ${activePlayer}` : 'Waiting for agents to join'}
            </p>
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
            Updates paused: {error}
          </div>
        )}
        {winner && (
          <div className="mb-4 rounded-xl border-2 border-amber-400 bg-amber-50 p-5 text-center shadow">
            <p className="text-sm font-bold uppercase tracking-widest text-amber-700">Game over</p>
            <p className="text-2xl font-black text-amber-950">
              🏆 {winner.nickname} wins with {winner.victory_points} victory points!
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(220px,1fr)_minmax(0,2.5fr)_minmax(220px,1fr)]">
          <aside className="order-1 min-h-0">
            <PlayerPanel players={leftPlayers} {...panelProps} />
          </aside>

          <section className="order-2 rounded-xl bg-white p-4 shadow">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-bold">Game board</h2>
              <div className="flex flex-wrap items-center gap-3">
                <div className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-blue-600">
                    Up next
                  </p>
                  <p className="text-sm font-semibold text-blue-950">
                    {nextPlayer ??
                      (activePlayer ? 'Waiting for the next turn' : 'Waiting for players')}
                  </p>
                </div>
                <div className="flex flex-wrap gap-3 text-xs">
                  {game.players.map((player) => (
                    <span key={player.nickname} className="flex items-center gap-1">
                      <i
                        className="h-3 w-3 rounded-full"
                        style={{ background: playerColors[player.nickname] }}
                      />
                      {player.nickname}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <GameBoard
              hexes={game.map}
              harbours={game.harbours}
              settlements={game.settlements}
              paths={game.paths}
              conquistadorLocation={game.conquistator_location}
              playerColors={playerColors}
            />
            <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
              <span className="text-sm font-semibold text-slate-600">Turns played</span>
              <strong className="text-lg text-slate-900">{game.turns_played}</strong>
            </div>
          </section>

          <aside className="order-3 min-h-0">
            <PlayerPanel players={rightPlayers} {...panelProps} />
          </aside>
        </div>

        <footer className="mt-4 rounded-lg bg-white p-3 text-xs text-slate-500 shadow-sm">
          <p>
            Game ID: <code>{gameId}</code>
          </p>
          {game.phase_deadline && (
            <p>Next timeout: {new Date(game.phase_deadline).toLocaleString()}</p>
          )}
        </footer>
      </div>
      <EventFeed events={events} connection={eventConnection} />
    </main>
  )
}

function GameNotFound({ gameId }: { gameId: string }) {
  return (
    <main className="min-h-screen grid place-items-center bg-slate-100 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-8 shadow">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-700">
          Simulation observer
        </p>
        <h1 className="mt-1 text-2xl font-bold text-red-600">Game not found</h1>
        <p className="mt-2 break-all text-slate-600">
          The server has no game with id <code>{gameId}</code>.
        </p>
        <p className="mt-2 text-slate-600">
          Games are kept in memory, so ids from an earlier server run stop working once it restarts.
          Use the id printed by the current <code>teyuna-simulate</code> run.
        </p>
        <a
          href="/"
          className="mt-5 inline-block rounded bg-blue-600 px-4 py-2 font-semibold text-white"
        >
          Watch another game
        </a>
      </div>
    </main>
  )
}

function GameFinder() {
  const [id, setId] = useState('')
  return (
    <main className="min-h-screen grid place-items-center bg-slate-100 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-8 shadow">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-700">
          Simulation observer
        </p>
        <h1 className="mt-1 text-2xl font-bold">Watch a Teyuna game</h1>
        <p className="mt-2 text-slate-600">
          Paste the game ID printed by <code>teyuna-simulate</code>. No player login is required.
        </p>
        <form
          className="mt-5 flex gap-2"
          onSubmit={(event) => {
            event.preventDefault()
            if (id.trim()) window.location.search = `?gameId=${encodeURIComponent(id.trim())}`
          }}
        >
          <input
            aria-label="Game ID"
            value={id}
            onChange={(event) => setId(event.target.value)}
            placeholder="Game ID"
            className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2"
          />
          <button className="rounded bg-blue-600 px-4 py-2 font-semibold text-white">Watch</button>
        </form>
      </div>
    </main>
  )
}

export default App
