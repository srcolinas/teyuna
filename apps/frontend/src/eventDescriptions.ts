export function describeEvent(data: Record<string, unknown>): string {
  switch (data.type) {
    case 'message':
      if (typeof data.by === 'string' && typeof data.text === 'string') {
        return `${data.by} sent a message: ${data.text}`
      }
      break
    case 'failed_action':
      if (typeof data.by === 'string' && typeof data.error === 'string') {
        const automatic = data.due_to_timeout === true ? ' automatically (timeout)' : ''
        return `${data.by}'s action failed${automatic}: ${data.error}`
      }
      break
    case 'successful_action':
      if (typeof data.by === 'string' && isRecord(data.result)) {
        return describeSuccessfulAction(
          data.by,
          data.due_to_timeout === true,
          isRecord(data.action) ? data.action : {},
          data.result,
        )
      }
      break
    case 'phase_changed':
      if (typeof data.previous_phase === 'string' && typeof data.next_phase === 'string') {
        return `Phase changed from ${data.previous_phase} to ${data.next_phase}.`
      }
      break
    case 'turn_changed': {
      const previous =
        data.previous_player == null
          ? 'nobody'
          : typeof data.previous_player === 'string'
            ? data.previous_player
            : null
      const next =
        data.next_player == null
          ? 'nobody'
          : typeof data.next_player === 'string'
            ? data.next_player
            : null
      if (previous !== null && next !== null) {
        return `Turn changed from ${previous} to ${next}.`
      }
      break
    }
    case 'biggest_army_changed':
      if (
        typeof data.previous_size === 'number' &&
        typeof data.current_size === 'number' &&
        (data.previous_holder == null || typeof data.previous_holder === 'string') &&
        (data.current_holder == null || typeof data.current_holder === 'string')
      ) {
        const previous = data.previous_holder ?? 'nobody'
        const current = data.current_holder ?? 'nobody'
        return `Biggest army changed from ${previous} (${data.previous_size}) to ${current} (${data.current_size}).`
      }
      break
    case 'longest_road_changed':
      if (
        typeof data.previous_length === 'number' &&
        typeof data.current_length === 'number' &&
        (data.previous_holder == null || typeof data.previous_holder === 'string') &&
        (data.current_holder == null || typeof data.current_holder === 'string')
      ) {
        const previous = data.previous_holder ?? 'nobody'
        const current = data.current_holder ?? 'nobody'
        return `Longest road changed from ${previous} (${data.previous_length}) to ${current} (${data.current_length}).`
      }
      break
    case 'end_game':
      if (typeof data.reason === 'string') {
        if (typeof data.winner === 'string') {
          return `Game ended: ${data.winner} wins (${data.reason}).`
        }
        if (data.winner == null) {
          return `Game ended with no winner (${data.reason}).`
        }
      }
      break
  }
  return 'Unrecognized event'
}

function describeSuccessfulAction(
  actor: string,
  dueToTimeout: boolean,
  action: Record<string, unknown>,
  result: Record<string, unknown>,
): string {
  const automatic = dueToTimeout ? ' automatically (timeout)' : ''

  if (typeof result.error === 'string') {
    return `${actor}'s action failed: ${result.error}`
  }

  if (
    typeof action.text === 'string' &&
    result.proposal_id == null &&
    action.offer == null &&
    action.request == null
  ) {
    return `${actor} sent a message: ${action.text}`
  }

  if (Array.isArray(result.settlement) && Array.isArray(result.path)) {
    return `${actor} placed a terrace at ${coordinate(result.settlement)} and a path at ${coordinate(result.path)}${automatic}.`
  }

  if (
    typeof result.die_1 === 'number' &&
    typeof result.die_2 === 'number' &&
    typeof result.next_phase === 'string'
  ) {
    return `${actor} rolled ${result.die_1} + ${result.die_2} = ${result.die_1 + result.die_2}${automatic}. Next phase: ${result.next_phase}.`
  }

  if (typeof result.q === 'number' && typeof result.r === 'number') {
    return `${actor} moved the conquistator to (${result.q}, ${result.r})${automatic}.`
  }

  if (
    result.proposal_id &&
    typeof result.proposer === 'string' &&
    typeof result.acceptor === 'string'
  ) {
    return `${result.acceptor} accepted ${result.proposer}'s trade: ${resourceList(result.offer)} for ${resourceList(result.request)}.`
  }

  if (result.proposal_id && Array.isArray(action.to)) {
    return `${actor} offered ${resourceList(action.offer)} for ${resourceList(action.request)} to ${action.to.map(String).join(', ')}. The trade remains pending until an addressed agent can afford it.`
  }

  if (result.offers && result.requests && typeof result.rate === 'number') {
    return `${actor} traded ${result.rate} ${String(result.offers)} with the supply for 1 ${String(result.requests)}.`
  }

  if (result.count && typeof result.count === 'object') {
    return `${actor} discarded ${resourceList(result.count)} after a 7 was rolled${automatic}.`
  }

  if (result.item && result.coordinate) {
    return `${actor} built a ${String(result.item)} at ${coordinate(result.coordinate)}${automatic}.`
  }

  if (!result.item && result.coordinate) {
    return `${actor} built a path at ${coordinate(result.coordinate)}${automatic}.`
  }

  if (typeof result.resource === 'string') {
    return `${actor} played Wisdom of Mamo and took ${result.resource}${automatic}.`
  }

  if (Array.isArray(result.resources) && result.resources.length === 2) {
    return `${actor} played Blessing of Aluna and took ${String(result.resources[0])} and ${String(result.resources[1])}${automatic}.`
  }

  if (Array.isArray(result.paths)) {
    return `${actor} played Pathfinder and built paths at ${result.paths.map(coordinate).join('; ')}${automatic}.`
  }

  if (result.card) {
    return `${actor} acquired or played ${String(result.card)}${automatic}.`
  }

  if (typeof result.next_player === 'string' && result.next_player) {
    return `${actor} ended the turn. ${result.next_player} plays next.`
  }

  return `${actor} completed an action${automatic}.`
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
