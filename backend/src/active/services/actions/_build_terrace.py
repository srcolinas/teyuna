from .... import player
from ... import entities
from . import _errors
from . import _add_free_terrace


def build_terrace(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
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

    target = entities.canonical_vertex(q, r, direction)
    if target not in game.free_verticies or target in game.restricted_verticies:
        raise _errors.InvalidSettlementLocation

    paths = game.players[to].paths
    dq5, dr5 = entities.delta_to_neighbor((direction + 5) % 6)
    adjacent_edges = (
        entities.canonical_edge(q, r, (direction + 5) % 6),
        entities.canonical_edge(q, r, direction),
        entities.canonical_edge(q + dq5, r + dr5, (direction + 1) % 6),
    )
    if not any(edge in paths for edge in adjacent_edges):
        raise _errors.InvalidSettlementLocation

    _add_free_terrace.add_free_terrace(game, to, q=q, r=r, direction=direction)
    game.players[to].resources.update(
        {
            entities.ResourceCard.STONE: -1,
            entities.ResourceCard.WOOD: -1,
            entities.ResourceCard.COTTON: -1,
            entities.ResourceCard.MAIZE: -1,
        }
    )
