import { useEffect, useMemo, useState } from 'react'
import { ActiveGame, PrivatePlayerInfo } from './types'
import { apiClient, apiErrorMessage } from './api'
import GameBoard from './components/GameBoard'
import PlayerPanel from './components/PlayerPanel'
import EventFeed, { GameEvent } from './components/EventFeed'

function App() {
  const gameId = new URLSearchParams(window.location.search).get('gameId')
  const [game, setGame] = useState<ActiveGame | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [events, setEvents] = useState<GameEvent[]>([])
  const [eventConnection, setEventConnection] = useState<'connecting' | 'live' | 'waiting'>('connecting')
  const [playerTokens, setPlayerTokens] = useState<Record<string, string>>({})
  const [privatePlayerInfo, setPrivatePlayerInfo] = useState<Record<string, PrivatePlayerInfo>>({})
  const [privateErrors, setPrivateErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!gameId) {
      setLoading(false)
      return
    }

    const fetchGame = async () => {
      try {
        setGame(await apiClient.getGame(gameId))
        setError(null)
      } catch (err) {
        setError(`Failed to load game: ${apiErrorMessage(err)}`)
      } finally {
        setLoading(false)
      }
    }

    void fetchGame()
    const interval = window.setInterval(fetchGame, 2000)
    return () => window.clearInterval(interval)
  }, [gameId])

  useEffect(() => {
    if (!gameId) return
    const entries = Object.entries(playerTokens)
    if (entries.length === 0) return

    const fetchPrivateInfo = async () => {
      await Promise.all(entries.map(async ([nickname, token]) => {
        try {
          const info = await apiClient.getPrivatePlayerInfo(gameId, token)
          setPrivatePlayerInfo(current => ({ ...current, [nickname]: info }))
          setPrivateErrors(current => {
            const next = { ...current }
            delete next[nickname]
            return next
          })
        } catch (err) {
          setPrivatePlayerInfo(current => {
            const next = { ...current }
            delete next[nickname]
            return next
          })
          setPrivateErrors(current => ({ ...current, [nickname]: apiErrorMessage(err) }))
        }
      }))
    }

    void fetchPrivateInfo()
    const interval = window.setInterval(fetchPrivateInfo, 2000)
    return () => window.clearInterval(interval)
  }, [gameId, playerTokens])

  useEffect(() => {
    if (!gameId) return
    const source = new EventSource(`http://localhost:8000/games/${gameId}/events`)
    source.onopen = () => setEventConnection('live')
    source.onerror = () => setEventConnection('waiting')
    source.onmessage = event => {
      try {
        const data = JSON.parse(event.data) as Record<string, unknown>
        setEvents(current => [...current.slice(-99), { id: event.lastEventId || crypto.randomUUID(), data, receivedAt: new Date() }])
      } catch {
        setEvents(current => [...current.slice(-99), { id: event.lastEventId || crypto.randomUUID(), data: { message: event.data }, receivedAt: new Date() }])
      }
    }
    return () => source.close()
  }, [gameId])

  const playerColors = useMemo(() => {
    const palette = ['#ef4444', '#0891b2', '#d97706', '#7c3aed']
    return Object.fromEntries((game?.players ?? []).map((player, index) => [player.nickname, palette[index]]))
  }, [game?.players])

  const submitPlayerToken = (nickname: string, token: string) => {
    setPlayerTokens(current => ({ ...current, [nickname]: token }))
    setPrivateErrors(current => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
  }

  const clearPlayerToken = (nickname: string) => {
    setPlayerTokens(current => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
    setPrivatePlayerInfo(current => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
    setPrivateErrors(current => {
      const next = { ...current }
      delete next[nickname]
      return next
    })
  }

  if (!gameId) return <GameFinder />

  if (loading && !game) {
    return <div className="min-h-screen grid place-items-center bg-slate-100 text-lg">Loading simulation…</div>
  }

  if (!game) {
    return <div className="min-h-screen grid place-items-center bg-slate-100"><div className="rounded-xl bg-white p-8 shadow"><h1 className="text-xl font-bold text-red-600">Simulation unavailable</h1><p className="mt-2 text-slate-600">{error}</p></div></div>
  }

  const activePlayer = game.turn_order[0]
  const winner = game.phase === 'end game'
    ? [...game.players].sort((left, right) => right.victory_points - left.victory_points)[0]
    : null

  return (
    <main className="min-h-screen bg-slate-100 p-4 pb-24">
      <div className="mx-auto max-w-7xl">
        <header className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-emerald-700">Live agent simulation</p>
            <h1 className="text-3xl font-bold text-slate-900">Teyuna — The Lost City</h1>
          </div>
          <div className="rounded-lg bg-white px-4 py-2 text-right shadow-sm">
            <p className="text-xs uppercase text-slate-500">Current phase</p>
            <p className="font-bold text-blue-700">{game.phase.toUpperCase()}</p>
            <p className="text-sm text-slate-600">{activePlayer ? `Active agent: ${activePlayer}` : 'Waiting for agents to join'}</p>
          </div>
        </header>

        {error && <div className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Updates paused: {error}</div>}
        {winner && (
          <div className="mb-4 rounded-xl border-2 border-amber-400 bg-amber-50 p-5 text-center shadow">
            <p className="text-sm font-bold uppercase tracking-widest text-amber-700">Game over</p>
            <p className="text-2xl font-black text-amber-950">🏆 {winner.nickname} wins with {winner.victory_points} victory points!</p>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
          <section className="rounded-xl bg-white p-4 shadow lg:col-span-3">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xl font-bold">Game board</h2>
              <div className="flex flex-wrap gap-3 text-xs">
                {game.players.map(player => <span key={player.nickname} className="flex items-center gap-1"><i className="h-3 w-3 rounded-full" style={{ background: playerColors[player.nickname] }} />{player.nickname}</span>)}
              </div>
            </div>
            <GameBoard hexes={game.map} settlements={game.settlements} paths={game.paths} conquistadorLocation={game.conquistator_location} playerColors={playerColors} />
          </section>

          <aside>
            <PlayerPanel
              players={game.players}
              turnOrder={game.turn_order}
              currentPlayerIdx={0}
              playerColors={playerColors}
              privateInfo={privatePlayerInfo}
              privateErrors={privateErrors}
              revealedPlayers={new Set(Object.keys(playerTokens))}
              onTokenSubmit={submitPlayerToken}
              onTokenClear={clearPlayerToken}
            />
          </aside>
        </div>

        <footer className="mt-4 rounded-lg bg-white p-3 text-xs text-slate-500 shadow-sm">
          <p>Game ID: <code>{gameId}</code></p>
          {game.phase_deadline && <p>Next timeout: {new Date(game.phase_deadline).toLocaleString()}</p>}
        </footer>
      </div>
      <EventFeed events={events} connection={eventConnection} />
    </main>
  )
}

function GameFinder() {
  const [id, setId] = useState('')
  return (
    <main className="min-h-screen grid place-items-center bg-slate-100 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-8 shadow">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-700">Simulation observer</p>
        <h1 className="mt-1 text-2xl font-bold">Watch a Teyuna game</h1>
        <p className="mt-2 text-slate-600">Paste the game ID printed by <code>teyuna-players</code>. No player login is required.</p>
        <form className="mt-5 flex gap-2" onSubmit={event => { event.preventDefault(); if (id.trim()) window.location.search = `?gameId=${encodeURIComponent(id.trim())}` }}>
          <input aria-label="Game ID" value={id} onChange={event => setId(event.target.value)} placeholder="Game ID" className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2" />
          <button className="rounded bg-blue-600 px-4 py-2 font-semibold text-white">Watch</button>
        </form>
      </div>
    </main>
  )
}

export default App
