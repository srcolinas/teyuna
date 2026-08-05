import { describe, expect, it } from 'vitest'

import { describeEvent } from './eventDescriptions'

describe('describeEvent', () => {
  it('describes chat messages', () => {
    expect(describeEvent({ type: 'message', by: 'alice', text: 'hello' })).toBe(
      'alice sent a message: hello',
    )
  })

  it('describes failed actions using event actor and timeout metadata', () => {
    expect(
      describeEvent({
        type: 'failed_action',
        by: 'alice',
        due_to_timeout: true,
        action: { kind: 'advance' },
        error: 'not your turn',
      }),
    ).toBe("alice's action failed automatically (timeout): not your turn")
  })

  it('describes successful actions from the nested result', () => {
    expect(
      describeEvent({
        type: 'successful_action',
        by: 'bob',
        due_to_timeout: false,
        action: { kind: 'advance' },
        result: {
          kind: 'dice_roll',
          die_1: 3,
          die_2: 4,
          next_phase: 'trade and build',
        },
      }),
    ).toBe('bob rolled 3 + 4 = 7. Next phase: trade and build.')
  })

  it('describes phase, turn, army, road, and end-game events', () => {
    expect(
      describeEvent({
        type: 'phase_changed',
        previous_phase: 'lobby',
        next_phase: 'first placement',
      }),
    ).toBe('Phase changed from lobby to first placement.')

    expect(
      describeEvent({
        type: 'turn_changed',
        previous_player: null,
        next_player: 'alice',
      }),
    ).toBe('Turn changed from nobody to alice.')

    expect(
      describeEvent({
        type: 'biggest_army_changed',
        previous_holder: null,
        current_holder: 'alice',
        previous_size: 2,
        current_size: 3,
      }),
    ).toBe('Biggest army changed from nobody (2) to alice (3).')

    expect(
      describeEvent({
        type: 'longest_road_changed',
        previous_holder: 'alice',
        current_holder: null,
        previous_length: 5,
        current_length: 4,
      }),
    ).toBe('Longest road changed from alice (5) to nobody (4).')

    expect(
      describeEvent({
        type: 'end_game',
        winner: 'alice',
        reason: 'victory',
      }),
    ).toBe('Game ended: alice wins (victory).')

    expect(
      describeEvent({
        type: 'end_game',
        winner: null,
        reason: 'lobby_timeout',
      }),
    ).toBe('Game ended with no winner (lobby_timeout).')
  })

  it('returns unrecognized for unknown payloads', () => {
    expect(describeEvent({})).toBe('Unrecognized event')
    expect(describeEvent({ type: 'message', by: 1 })).toBe('Unrecognized event')
  })
})
