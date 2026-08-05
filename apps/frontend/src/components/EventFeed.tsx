import { useEffect, useRef, useState } from 'react'

import { describeEvent } from '../eventDescriptions'

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
