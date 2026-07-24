import collections
from typing import Final

import teyuna_core

from ... import entities, player
from . import _play_card


def handle_dice_roll(
    game: entities.Game, action: teyuna_core.PlayerAction
) -> teyuna_core.DiceRollResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_core.DiceRollResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    dice_1, dice_2 = action.rng_.randint(1, 6), action.rng_.randint(1, 6)
    total = dice_1 + dice_2
    produced: dict[player.Nickname, dict[teyuna_core.ResourceCard, int]] = {}

    if total == 7:
        game.to_discard_resources = {
            nick: total_resources // 2
            for nick, p in game.players.items()
            if (total_resources := sum(p.resources.values())) > 7
        }
        if game.to_discard_resources:
            phase = teyuna_core.GamePhaseName.DISCARD_RESOURCES
        else:
            phase = teyuna_core.GamePhaseName.MOVE_CONQUISTATOR
    else:
        produced = _produce_resources(game, roll=total)
        phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD

    game.phase = phase
    return teyuna_core.DiceRollResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        die_1=dice_1,
        die_2=dice_2,
        to_discard=dict(game.to_discard_resources),
        produced=produced,
    )


def handle_play_wisdom_card(
    game: entities.Game, action: teyuna_core.PlayWisdomCardAction
) -> teyuna_core.PlayedWisdomCardResult:
    return _play_card.play_wisdom_card(
        game,
        action,
        card_phases=_DICE_CARD_PHASES,
        phase_label="dice roll",
    )


_DICE_CARD_PHASES: Final[dict[teyuna_core.WisdomCard, teyuna_core.GamePhaseName]] = {
    teyuna_core.WisdomCard.WARRIOR: teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR,
    teyuna_core.WisdomCard.WINDOM_OF_MAMO: teyuna_core.GamePhaseName.DICE_PLAY_MAMO,
    teyuna_core.WisdomCard.BLESSING_OF_ALUNA: teyuna_core.GamePhaseName.DICE_PLAY_BLESSED,
    teyuna_core.WisdomCard.PATHFINDER: teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER,
    teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS: teyuna_core.GamePhaseName.DICE_ROLL,
}


def _produce_resources(
    game: entities.Game, *, roll: int
) -> dict[str, dict[teyuna_core.ResourceCard, int]]:
    produced: dict[str, collections.Counter[teyuna_core.ResourceCard]] = {}
    for hex_tile in game.map:
        if hex_tile.number != roll:
            continue
        if hex_tile.type is teyuna_core.HexType.DESERT:
            continue
        if (hex_tile.q, hex_tile.r) == (
            game.conquistator_location.q,
            game.conquistator_location.r,
        ):
            continue
        resource = teyuna_core.HEX_TYPE_TO_RESOURCE[hex_tile.type]
        for nickname in game.turn_order:
            settlements = game.players[nickname].settlements
            for direction in range(6):
                coord = teyuna_core.canonical_vertex(hex_tile.q, hex_tile.r, direction)
                if coord not in settlements:
                    continue
                settlement = settlements[coord]
                amount = 1 if settlement is teyuna_core.SettlementType.TERRACE else 2
                to_grant = min(amount, game.resource_supply[resource])
                if to_grant <= 0:
                    continue
                game.take_from_supply(
                    to=nickname,
                    amount=collections.Counter({resource: to_grant}),
                )
                produced.setdefault(
                    nickname, collections.Counter[teyuna_core.ResourceCard]()
                )[resource] += to_grant
    return {nick: dict(counts) for nick, counts in produced.items()}
