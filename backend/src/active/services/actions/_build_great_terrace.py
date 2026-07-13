from .... import player
from ... import entities
from . import _errors


def build_great_terrace(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
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
    settlements = game.players[to].settlements
    if coord not in settlements:
        raise _errors.InvalidSettlementLocation(
            "You must first build a terrace at specified location."
        )

    if settlements[coord] is entities.SettlementType.GREAT_TERRACE:
        raise _errors.InvalidSettlementLocation(
            "You have already built a great terrace at specified location."
        )

    game.players[to].settlements[coord] = entities.SettlementType.GREAT_TERRACE
    game.players[to].resources.update(
        {
            entities.ResourceCard.GOLD: -3,
            entities.ResourceCard.MAIZE: -2,
        }
    )
    game.resource_supply.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
