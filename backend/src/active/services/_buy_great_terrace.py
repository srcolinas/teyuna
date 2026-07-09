import collections

from ... import player
from .. import entities
from . import _errors


def buy_great_terrace(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
    if to != game.turn_order[0]:
        raise _errors.PlayerNotInTurn

    resources = game.players[to].resources
    if resources[entities.ResourceCard.GOLD] < 3:
        raise _errors.InsufficientResources
    if resources[entities.ResourceCard.MAIZE] < 2:
        raise _errors.InsufficientResources

    if (
        game.players[to].settlements.count(entities.SettlementType.GREAT_TERRACE)
        >= entities.MAX_GREAT_TERRACES
    ):
        raise _errors.InsufficientResources

    coord = entities.canonical_vertex(q, r, direction)
    if (
        coord not in game.players[to].settlements
        or game.players[to].settlements[coord] is not entities.SettlementType.TERRACE
    ):
        raise _errors.InvalidSettlementLocation(
            "You must first build a terrace at specified location."
        )

    game.upgrade_terrace(to, q=q, r=r, direction=direction)
    game.discount_resources(
        to,
        resources=collections.Counter(
            {
                entities.ResourceCard.GOLD: 3,
                entities.ResourceCard.MAIZE: 2,
            }
        ),
    )
