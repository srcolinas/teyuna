from .... import player
from ... import entities
from . import _errors


def add_free_terrace(
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

    target = entities.canonical_vertex(q, r, direction)
    game.players[to].settlements[target] = entities.SettlementType.TERRACE
    game.free_verticies.remove(target)
    dq5, dr5 = entities.delta_to_neighbor((direction + 5) % 6)
    blocked_vertices = [
        (q, r, (direction + 1) % 6),
        (q, r, (direction + 5) % 6),
        (q + dq5, r + dr5, (direction + 1) % 6),
    ]
    for vq, vr, vd in blocked_vertices:
        vertex = entities.canonical_vertex(vq, vr, vd)
        game.restricted_verticies.add(vertex)
