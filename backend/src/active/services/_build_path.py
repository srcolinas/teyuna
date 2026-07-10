import collections

from ... import player
from .. import entities
from . import _errors, _helpers, _map


def build_path(
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

    resources = game.players[to].resources
    if resources[entities.ResourceCard.STONE] < 1:
        raise _errors.InsufficientResources

    if resources[entities.ResourceCard.WOOD] < 1:
        raise _errors.InsufficientResources

    _add_path(game, to, q=q, r=r, direction=direction)
    _helpers.discount_resources(
        game,
        to,
        resources=collections.Counter(
            {
                entities.ResourceCard.STONE: 1,
                entities.ResourceCard.WOOD: 1,
            }
        ),
    )


def _add_path(
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

    if len(game.players[to].paths) >= entities.MAX_PATHS:
        raise _errors.InsufficientResources

    target = _map.canonical_edge(q, r, direction)
    if target not in game.free_edges:
        raise _errors.InvalidPathLocation

    this_player = game.players[to]
    settlements = this_player.settlements
    paths = this_player.paths
    free_verticies = game.free_verticies

    forbidden = True
    q, r, direction = target
    vertices = [
        _map.canonical_vertex(q, r, direction),
        _map.canonical_vertex(q, r, (direction + 1) % 6),
    ]
    for v in vertices:
        if v in settlements:
            forbidden = False
            break
        if v in free_verticies:
            vq, vr, vd = v
            dq5, dr5 = _map.delta_to_neighbor((vd + 5) % 6)
            for e in (
                _map.canonical_edge(vq, vr, (vd + 5) % 6),
                _map.canonical_edge(vq, vr, vd),
                _map.canonical_edge(vq + dq5, vr + dr5, (vd + 1) % 6),
            ):
                if e != target and e in paths:
                    forbidden = False
                    break

    if forbidden:
        raise _errors.InvalidPathLocation

    game.free_edges.remove(target)
    game.players[to].paths.add(target)
