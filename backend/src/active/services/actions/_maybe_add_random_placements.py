import random

from .... import player
from ... import entities
from . import _add_free_path, _add_free_terrace

_RND: random.Random = random.Random()


def maybe_add_random_placements(
    game: entities.ActiveGame,
    expected_count: int,
    rnd: random.Random = _RND,
) -> None:
    nickname = game.active_player
    player_state = game.players[nickname]
    if player_state.settlements.count(entities.SettlementType.TERRACE) < expected_count:
        location = _add_random_free_terrace(game, nickname, rnd)
        if location is not None:
            _add_path_next_to_terrace(game, nickname, location, rnd)
    elif len(player_state.paths) < expected_count:
        lonely_terrace = _find_lonely_terrace(game, nickname, rnd=rnd)
        if lonely_terrace is not None:
            _add_path_next_to_terrace(game, nickname, lonely_terrace, rnd)


def _add_random_free_terrace(
    game: entities.ActiveGame,
    nickname: player.Nickname,
    rnd: random.Random = _RND,
) -> entities.Coordinate | None:
    locations = [
        coord for coord in game.free_verticies if coord not in game.restricted_verticies
    ]
    if not locations:
        return None

    coord = rnd.choice(locations)
    _add_free_terrace.add_free_terrace(
        game, nickname, q=coord.q, r=coord.r, direction=coord.d
    )
    return coord


def _find_lonely_terrace(
    game: entities.ActiveGame,
    nickname: player.Nickname,
    rnd: random.Random = _RND,
) -> entities.Coordinate | None:
    paths = game.players[nickname].paths
    lonely: list[entities.Coordinate] = []
    for coord, settlement_type in game.players[nickname].settlements.items():
        if settlement_type is not entities.SettlementType.TERRACE:
            continue
        adjacent_edges = _edges_adjacent_to_vertex(coord.q, coord.r, coord.d)
        if not any(edge in paths for edge in adjacent_edges):
            lonely.append(coord)
    if not lonely:
        return None
    return rnd.choice(lonely)


def _add_path_next_to_terrace(
    game: entities.ActiveGame,
    nickname: player.Nickname,
    terrace: entities.Coordinate,
    rnd: random.Random = _RND,
) -> None:
    locations = _path_locations_next_to_terrace(game, nickname, terrace)
    if not locations:
        return

    coord = rnd.choice(locations)
    _add_free_path.add_free_path(
        game, nickname, q=coord.q, r=coord.r, direction=coord.d
    )


def _path_locations_next_to_terrace(
    game: entities.ActiveGame,
    nickname: player.Nickname,
    terrace: entities.Coordinate,
) -> list[entities.Coordinate]:
    return [
        edge
        for edge in _edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d)
        if edge in game.free_edges and _is_valid_path_location(game, nickname, edge)
    ]


def _edges_adjacent_to_vertex(
    q: int, r: int, direction: int
) -> set[entities.Coordinate]:
    dq5, dr5 = entities.delta_to_neighbor((direction + 5) % 6)
    return {
        entities.canonical_edge(q, r, (direction + 5) % 6),
        entities.canonical_edge(q, r, direction),
        entities.canonical_edge(q + dq5, r + dr5, (direction + 1) % 6),
    }


def _is_valid_path_location(
    game: entities.ActiveGame,
    nickname: player.Nickname,
    target: entities.Coordinate,
) -> bool:
    settlements = game.players[nickname].settlements
    paths = game.players[nickname].paths
    free_verticies = game.free_verticies

    q, r, direction = target
    vertices = (
        entities.canonical_vertex(q, r, direction),
        entities.canonical_vertex(q, r, (direction + 1) % 6),
    )
    for vertex in vertices:
        if vertex in settlements:
            return True
        if vertex in free_verticies:
            vq, vr, vd = vertex
            dq5, dr5 = entities.delta_to_neighbor((vd + 5) % 6)
            for edge in (
                entities.canonical_edge(vq, vr, (vd + 5) % 6),
                entities.canonical_edge(vq, vr, vd),
                entities.canonical_edge(vq + dq5, vr + dr5, (vd + 1) % 6),
            ):
                if edge != target and edge in paths:
                    return True
    return False
