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
      <button onClick={() => setOpen(value => !value)} className="flex w-full items-center justify-between bg-slate-900 px-4 py-3 text-left text-white">
        <span><span className="mr-2">💬</span><strong>Game events</strong></span>
        <span className="flex items-center gap-2 text-xs"><i className={`h-2 w-2 rounded-full ${connection === 'live' ? 'bg-green-400' : connection === 'connecting' ? 'bg-amber-300' : 'bg-red-400'}`} />{connection === 'live' ? 'Live' : connection === 'connecting' ? 'Connecting' : 'Waiting for active game'} <span>{open ? '▼' : '▲'}</span></span>
      </button>
      {open && (
        <div ref={feed} className="h-72 overflow-y-auto bg-slate-50 p-3" aria-live="polite">
          {events.length === 0 && <p className="rounded-lg bg-white p-3 text-sm text-slate-500">Events will appear here as agents act. Events emitted before this panel connected are not replayed.</p>}
          <ol className="space-y-2">
            {events.map(event => (
              <li key={`${event.id}-${event.receivedAt.getTime()}`} className="rounded-lg bg-white p-3 text-sm shadow-sm">
                <time className="block text-[11px] text-slate-400">{event.receivedAt.toLocaleTimeString()}</time>
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
  const actor = typeof data.by === 'string' ? data.by : 'The game'
  const automatic = data.due_to_timeout === true ? ' automatically (timeout)' : ''
  if (data.succeeded === false) return `${actor}'s action failed: ${String(data.error ?? 'unknown error')}`
  if (Array.isArray(data.settlement) && Array.isArray(data.path)) return `${actor} placed a terrace at ${coordinate(data.settlement)} and a path at ${coordinate(data.path)}${automatic}.`
  if (typeof data.die_1 === 'number' && typeof data.die_2 === 'number') return `${actor} rolled ${data.die_1} + ${data.die_2} = ${data.die_1 + data.die_2}${automatic}. Next phase: ${String(data.phase)}.`
  if (typeof data.q === 'number' && typeof data.r === 'number') return `${actor} moved the conquistator to (${data.q}, ${data.r})${automatic}.`
  if (data.proposal_id && data.proposer && data.acceptor) return `${String(data.acceptor)} accepted ${String(data.proposer)}'s trade: ${resourceList(data.offer)} for ${resourceList(data.request)}.`
  if (data.proposal_id) return `${actor} offered ${resourceList(data.offer)} for ${resourceList(data.request)} to ${Array.isArray(data.to) ? data.to.join(', ') : 'the other agents'}. The trade remains pending until an addressed agent can afford it.`
  if (data.offers && data.requests && data.rate) return `${actor} traded ${data.rate} ${String(data.offers)} with the supply for 1 ${String(data.requests)}.`
  if (data.count && typeof data.count === 'object') return `${actor} discarded ${resourceList(data.count)} after a 7 was rolled${automatic}.`
  if (data.item && data.coordinate) return `${actor} built a ${String(data.item)} at ${coordinate(data.coordinate)}${automatic}.`
  if (data.card) return `${actor} acquired or played ${String(data.card)}${automatic}.`
  if (data.next_player) return `${actor} ended the turn. ${String(data.next_player)} plays next.`
  return `${actor} completed an action${automatic}. Phase: ${String(data.phase ?? 'unknown')}.`
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
