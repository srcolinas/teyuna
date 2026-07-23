interface GamePhasePanelProps {
  phase: string
  activePlayer: string
  currentNickname: string | null
  onAdvanceTurn: () => void
  onRollDice: () => void
  onBuyWisdomCard: () => void
  onChooseBuild: (item: 'terrace' | 'great terrace' | 'path') => void
  loading: boolean
}

export default function GamePhasePanel({
  phase,
  activePlayer,
  currentNickname,
  onAdvanceTurn,
  onRollDice,
  onBuyWisdomCard,
  onChooseBuild,
  loading,
}: GamePhasePanelProps) {
  const isCurrentPlayerActive = currentNickname === activePlayer
  const phaseText = phase.replace(/_/g, ' ').toUpperCase()
  const isDiceRoll = phase === 'dice roll'
  const isTradeAndBuild = phase === 'trade and build'
  const isPlacement = phase === 'first placement' || phase === 'second placement'
  const isMoveConquistator = phase === 'move conquistator'

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-xl font-bold mb-4">Game Status</h2>

      <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
        <div className="text-sm text-gray-600">Current Phase</div>
        <div className="text-lg font-bold text-blue-700">{phaseText}</div>
      </div>

      <div className="mb-4 p-3 bg-green-50 rounded border border-green-200">
        <div className="text-sm text-gray-600">Active Player</div>
        <div className="text-lg font-bold text-green-700">{activePlayer}</div>
        {isCurrentPlayerActive && (
          <div className="text-xs text-green-600 mt-1">👤 This is you!</div>
        )}
      </div>

      <div className="space-y-2">
        {isPlacement && (
          <p className="text-sm text-gray-700">
            Click an empty board corner, then an adjacent edge.
          </p>
        )}
        {isMoveConquistator && (
          <p className="text-sm text-gray-700">Click a different hex to move the conquistator.</p>
        )}

        {isDiceRoll && (
          <button
            onClick={onRollDice}
            disabled={!isCurrentPlayerActive || loading}
            className="w-full px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:bg-gray-300 font-semibold"
          >
            🎲 Roll Dice
          </button>
        )}

        {isTradeAndBuild && (
          <>
            <button
              onClick={() => onChooseBuild('terrace')}
              disabled={!isCurrentPlayerActive || loading}
              className="w-full px-4 py-2 bg-emerald-600 text-white rounded disabled:bg-gray-300 font-semibold"
            >
              Build Terrace
            </button>
            <button
              onClick={() => onChooseBuild('great terrace')}
              disabled={!isCurrentPlayerActive || loading}
              className="w-full px-4 py-2 bg-teal-700 text-white rounded disabled:bg-gray-300 font-semibold"
            >
              Upgrade to Great Terrace
            </button>
            <button
              onClick={() => onChooseBuild('path')}
              disabled={!isCurrentPlayerActive || loading}
              className="w-full px-4 py-2 bg-stone-600 text-white rounded disabled:bg-gray-300 font-semibold"
            >
              Build Path
            </button>
            <button
              onClick={onBuyWisdomCard}
              disabled={!isCurrentPlayerActive || loading}
              className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-300 font-semibold"
            >
              🃏 Buy Wisdom Card
            </button>
            <button
              onClick={onAdvanceTurn}
              disabled={!isCurrentPlayerActive || loading}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 font-semibold"
            >
              ➡️ End Turn
            </button>
          </>
        )}

        {!isCurrentPlayerActive && activePlayer && (
          <p className="text-sm text-amber-700">Waiting for {activePlayer}.</p>
        )}
      </div>

      {loading && (
        <div className="mt-4 text-center text-gray-500">
          <div className="inline-block animate-spin">⏳</div> Loading...
        </div>
      )}
    </div>
  )
}
