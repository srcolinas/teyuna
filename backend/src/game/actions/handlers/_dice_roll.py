import collections
from typing import Final

import pydantic

from ... import player
from ... import entities
from .. import _registry
from ._play_card import PlayWisdomCardAction, PlayedWisdomCardResult, play_wisdom_card


class DiceRollResult(_registry.ActionExecutionResult):
    die_1: int = -1
    die_2: int = -1
    to_discard: dict[player.Nickname, int] = pydantic.Field(default_factory=dict)
    produced: dict[player.Nickname, dict[entities.ResourceCard, int]] = pydantic.Field(
        default_factory=dict
    )


def handle_dice_roll(
    game: entities.Game, action: _registry.PlayerAction
) -> DiceRollResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return DiceRollResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    dice_1, dice_2 = action.rng_.randint(1, 6), action.rng_.randint(1, 6)
    total = dice_1 + dice_2
    produced: dict[player.Nickname, dict[entities.ResourceCard, int]] = {}

    if total == 7:
        game.to_discard_resources = {
            nick: total_resources // 2
            for nick, p in game.players.items()
            if (total_resources := sum(p.resources.values())) > 7
        }
        if game.to_discard_resources:
            phase = entities.GamePhaseName.DISCARD_RESOURCES
        else:
            phase = entities.GamePhaseName.MOVE_CONQUISTATOR
    else:
        produced = _produce_resources(game, roll=total)
        phase = entities.GamePhaseName.TRADE_AND_BUILD

    game.phase = phase
    return DiceRollResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        die_1=dice_1,
        die_2=dice_2,
        to_discard=dict(game.to_discard_resources),
        produced=produced,
    )


def handle_play_wisdom_card(
    game: entities.Game, action: PlayWisdomCardAction
) -> PlayedWisdomCardResult:
    return play_wisdom_card(
        game,
        action,
        card_phases=_DICE_CARD_PHASES,
        phase_label="dice roll",
    )


_DICE_CARD_PHASES: Final[dict[entities.WisdomCard, entities.GamePhaseName]] = {
    entities.WisdomCard.WARRIOR: entities.GamePhaseName.DICE_PLAY_WARRIOR,
    entities.WisdomCard.WINDOM_OF_MAMO: entities.GamePhaseName.DICE_PLAY_MAMO,
    entities.WisdomCard.BLESSING_OF_ALUNA: entities.GamePhaseName.DICE_PLAY_BLESSED,
    entities.WisdomCard.PATHFINDER: entities.GamePhaseName.DICE_PLAY_PATHFINDER,
    entities.WisdomCard.LEGACY_OF_THE_ELDERS: entities.GamePhaseName.DICE_ROLL,
}


def _produce_resources(
    game: entities.Game, *, roll: int
) -> dict[player.Nickname, dict[entities.ResourceCard, int]]:
    produced: dict[player.Nickname, collections.Counter[entities.ResourceCard]] = {}
    for hex_tile in game.map:
        if hex_tile.number != roll:
            continue
        if hex_tile.type is entities.HexType.DESERT:
            continue
        if (hex_tile.q, hex_tile.r) == (
            game.conquistator_location.q,
            game.conquistator_location.r,
        ):
            continue
        resource = entities.HEX_TYPE_TO_RESOURCE[hex_tile.type]
        for nickname in game.turn_order:
            settlements = game.players[nickname].settlements
            for direction in range(6):
                coord = entities.canonical_vertex(hex_tile.q, hex_tile.r, direction)
                if coord not in settlements:
                    continue
                settlement = settlements[coord]
                amount = 1 if settlement is entities.SettlementType.TERRACE else 2
                to_grant = min(amount, game.resource_supply[resource])
                if to_grant <= 0:
                    continue
                game.take_from_supply(
                    to=nickname,
                    amount=collections.Counter({resource: to_grant}),
                )
                produced.setdefault(nickname, collections.Counter())[resource] += (
                    to_grant
                )
    return {nick: dict(counts) for nick, counts in produced.items()}
