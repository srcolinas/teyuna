import collections

from ... import player
from .. import entities
from . import _errors


def buy_terrace(
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
    if resources[entities.ResourceCard.STONE] < 1:
        raise _errors.InsufficientResources

    if resources[entities.ResourceCard.WOOD] < 1:
        raise _errors.InsufficientResources

    if resources[entities.ResourceCard.COTTON] < 1:
        raise _errors.InsufficientResources

    if resources[entities.ResourceCard.MAIZE] < 1:
        raise _errors.InsufficientResources

    if (
        game.players[to].settlements.count(entities.SettlementType.TERRACE)
        >= entities.MAX_TERRACES
    ):
        raise _errors.InsufficientResources

    _add_terrace(game, to, q=q, r=r, direction=direction)
    game.discount_resources(
        to,
        resources=collections.Counter(
            {
                entities.ResourceCard.STONE: 1,
                entities.ResourceCard.WOOD: 1,
                entities.ResourceCard.COTTON: 1,
                entities.ResourceCard.MAIZE: 1,
            }
        ),
    )


def _add_terrace(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
    target = entities.canonical_vertex(q, r, direction)
    if target not in game.free_verticies or target in game.restricted_verticies:
        raise _errors.InvalidSettlementLocation

    paths = game.players[to].paths
    dq5, dr5 = entities.NEIGHBOR[(direction + 5) % 6]
    adjacent_edges = (
        entities.canonical_edge(q, r, (direction + 5) % 6),
        entities.canonical_edge(q, r, direction),
        entities.canonical_edge(q + dq5, r + dr5, (direction + 1) % 6),
    )
    if not any(edge in paths for edge in adjacent_edges):
        raise _errors.InvalidSettlementLocation

    game.add_terrace(to, q=q, r=r, direction=direction)
