import { useEffect, useRef, useState } from 'react'

export interface GameEvent {
  id: string
  data: Record<string, unknown>
  receivedAt: Date
}

interface EventFeedProps {
  events: GameEvent[]
  connection: 'connecting' | 'live' | 'waiting'
}

export default function EventFeed({ events, connection }: EventFeedProps) {
  const [open, setOpen] = useState(true)
  const feed = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (feed.current) feed.current.scrollTop = feed.current.scrollHeight
  }, [events])

  return (
    <section className="fixed bottom-4 right-4 z-20 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
      <button
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between bg-slate-900 px-4 py-3 text-left text-white"
      >
        <span>
          <span className="mr-2">💬</span>
          <strong>Game events</strong>
        </span>
        <span className="flex items-center gap-2 text-xs">
          <i
            className={`h-2 w-2 rounded-full ${connection === 'live' ? 'bg-green-400' : connection === 'connecting' ? 'bg-amber-300' : 'bg-red-400'}`}
          />
          {connection === 'live'
            ? 'Live'
            : connection === 'connecting'
              ? 'Connecting'
              : 'Waiting for active game'}{' '}
          <span>{open ? '▼' : '▲'}</span>
        </span>
      </button>
      {open && (
        <div ref={feed} className="h-72 overflow-y-auto bg-slate-50 p-3" aria-live="polite">
          {events.length === 0 && (
            <p className="rounded-lg bg-white p-3 text-sm text-slate-500">
              Events will appear here as agents act. Events emitted before this panel connected are
              not replayed.
            </p>
          )}
          <ol className="space-y-2">
            {events.map((event) => (
              <li
                key={`${event.id}-${event.receivedAt.getTime()}`}
                className="rounded-lg bg-white p-3 text-sm shadow-sm"
              >
                <time className="block text-[11px] text-slate-400">
                  {event.receivedAt.toLocaleTimeString()}
                </time>
                <p className="mt-1 text-slate-700">{describeEvent(event.data)}</p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  )
}

function describeEvent(data: Record<string, unknown>): string {
  if (!isRecord(data.action) || typeof data.action.by !== 'string') {
    return 'Unrecognized event'
  }
  const action = data.action
  const actor = action.by
  const automatic = action.due_to_timeout === true ? ' automatically (timeout)' : ''

  if (typeof data.error === 'string') {
    return `${actor}'s action failed: ${data.error}`
  }

  if (
    typeof action.text === 'string' &&
    data.proposal_id == null &&
    action.offer == null &&
    action.request == null
  ) {
    return `${actor} sent a message: ${action.text}`
  }

  if (Array.isArray(data.settlement) && Array.isArray(data.path)) {
    return `${actor} placed a terrace at ${coordinate(data.settlement)} and a path at ${coordinate(data.path)}${automatic}.`
  }

  if (
    typeof data.die_1 === 'number' &&
    typeof data.die_2 === 'number' &&
    typeof data.next_phase === 'string'
  ) {
    return `${actor} rolled ${data.die_1} + ${data.die_2} = ${data.die_1 + data.die_2}${automatic}. Next phase: ${data.next_phase}.`
  }

  if (typeof data.q === 'number' && typeof data.r === 'number') {
    return `${actor} moved the conquistator to (${data.q}, ${data.r})${automatic}.`
  }

  if (data.proposal_id && typeof data.proposer === 'string' && typeof data.acceptor === 'string') {
    return `${data.acceptor} accepted ${data.proposer}'s trade: ${resourceList(data.offer)} for ${resourceList(data.request)}.`
  }

  if (data.proposal_id && Array.isArray(action.to)) {
    return `${actor} offered ${resourceList(action.offer)} for ${resourceList(action.request)} to ${action.to.map(String).join(', ')}. The trade remains pending until an addressed agent can afford it.`
  }

  if (data.offers && data.requests && typeof data.rate === 'number') {
    return `${actor} traded ${data.rate} ${String(data.offers)} with the supply for 1 ${String(data.requests)}.`
  }

  if (data.count && typeof data.count === 'object') {
    return `${actor} discarded ${resourceList(data.count)} after a 7 was rolled${automatic}.`
  }

  if (data.item && data.coordinate) {
    return `${actor} built a ${String(data.item)} at ${coordinate(data.coordinate)}${automatic}.`
  }

  if (!data.item && data.coordinate) {
    return `${actor} built a path at ${coordinate(data.coordinate)}${automatic}.`
  }

  if (typeof data.resource === 'string') {
    return `${actor} played Wisdom of Mamo and took ${data.resource}${automatic}.`
  }

  if (Array.isArray(data.resources) && data.resources.length === 2) {
    return `${actor} played Blessing of Aluna and took ${String(data.resources[0])} and ${String(data.resources[1])}${automatic}.`
  }

  if (Array.isArray(data.paths)) {
    return `${actor} played Pathfinder and built paths at ${data.paths.map(coordinate).join('; ')}${automatic}.`
  }

  if (data.card) {
    return `${actor} acquired or played ${String(data.card)}${automatic}.`
  }

  if (typeof data.next_player === 'string' && data.next_player) {
    return `${actor} ended the turn. ${data.next_player} plays next.`
  }

  return 'Unrecognized event'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function resourceList(value: unknown): string {
  if (!value || typeof value !== 'object') return String(value)
  return Object.entries(value as Record<string, unknown>)
    .map(([resource, count]) => `${String(count)} ${resource}`)
    .join(', ')
}

function coordinate(value: unknown): string {
  if (Array.isArray(value)) return `(${value.join(', ')})`
  if (value && typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
