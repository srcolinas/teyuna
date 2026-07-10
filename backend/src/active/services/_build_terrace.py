from ... import player
from .. import entities
from . import _errors, _map


def add_initial_terrace(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
    if game.phase is not entities.GamePhase.INITIAL:
        raise _errors.InvalidGamePhase

    if to != game.turn_order[0]:
        raise _errors.PlayerNotInTurn

    target = _map.canonical_vertex(q, r, direction)
    if target not in game.free_verticies or target in game.restricted_verticies:
        raise _errors.InvalidSettlementLocation

    _add_terrace_unrestricted(game, to, q=q, r=r, direction=direction)


def build_terrace(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
    if game.phase is not entities.GamePhase.MAIN:
        raise _errors.InvalidGamePhase

    if game.turn_phase is not entities.TurnPhase.CONSTRUCTION:
        raise _errors.InvalidGamePhase

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

    target = _map.canonical_vertex(q, r, direction)
    if target not in game.free_verticies or target in game.restricted_verticies:
        raise _errors.InvalidSettlementLocation

    paths = game.players[to].paths
    dq5, dr5 = _map.delta_to_neighbor((direction + 5) % 6)
    adjacent_edges = (
        _map.canonical_edge(q, r, (direction + 5) % 6),
        _map.canonical_edge(q, r, direction),
        _map.canonical_edge(q + dq5, r + dr5, (direction + 1) % 6),
    )
    if not any(edge in paths for edge in adjacent_edges):
        raise _errors.InvalidSettlementLocation

    _add_terrace_unrestricted(game, to, q=q, r=r, direction=direction)
    game.players[to].resources.update(
        {
            entities.ResourceCard.STONE: -1,
            entities.ResourceCard.WOOD: -1,
            entities.ResourceCard.COTTON: -1,
            entities.ResourceCard.MAIZE: -1,
        }
    )


def _add_terrace_unrestricted(
    game: entities.ActiveGame, to: player.Nickname, /, *, q: int, r: int, direction: int
) -> None:
    target = _map.canonical_vertex(q, r, direction)
    game.players[to].settlements[target] = entities.SettlementType.TERRACE
    game.free_verticies.remove(target)
    dq5, dr5 = _map.delta_to_neighbor((direction + 5) % 6)
    blocked_vertices = [
        (q, r, (direction + 1) % 6),
        (q, r, (direction + 5) % 6),
        (q + dq5, r + dr5, (direction + 1) % 6),
    ]
    for vq, vr, vd in blocked_vertices:
        vertex = _map.canonical_vertex(vq, vr, vd)
        game.restricted_verticies.add(vertex)
