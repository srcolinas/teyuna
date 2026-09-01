import datetime
import random
import uuid
from collections.abc import Iterator
from typing import Final, Protocol

import teyuna_core

from .. import entities
from . import _retrieve


class CreateGameRepository(_retrieve.RetrieveGameRepository, Protocol):
    def add(
        self,
        game: entities.Game,
    ) -> uuid.UUID: ...


def create_game(
    params: teyuna_core.CreateGameRequest,
    repository: CreateGameRepository,
    *,
    lobby_timeout: datetime.timedelta,
    now: datetime.datetime | None = None,
) -> teyuna_core.Game:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)
    board, conquistator, harbours = _resolve_board(params)
    game = entities.Game(
        map=board,
        conquistator_location=conquistator,
        harbours=harbours,
        players={},
        available_slots=params.num_players,
        phase=teyuna_core.GamePhaseName.LOBBY,
        phase_deadline=now + lobby_timeout,
    )
    game_id = repository.add(game)
    return _retrieve.retrieve_game(game_id, repository=repository)


def generate_map() -> tuple[teyuna_core.MapHex, ...]:
    coords = [
        (q, r)
        for q in range(-2, 3)
        for r in range(-2, 3)
        if (q, r) not in teyuna_core.INVALID_HEX_COORDINATES
    ]
    types = list(_TYPES)
    random.shuffle(types)
    hex_types = dict(zip(coords, types, strict=True))
    numbered = [c for c in coords if hex_types[c] is not teyuna_core.HexType.DESERT]

    for _ in range(_MAX_MAP_ATTEMPTS):
        numbers = list(_NUMBERS)
        random.shuffle(numbers)
        number_by_coord = {(q, r): 7 for (q, r) in coords}
        number_by_coord.update(zip(numbered, numbers, strict=True))
        if _reds_are_separated(number_by_coord):
            break
    else:
        raise RuntimeError("could not generate a valid map layout")

    return tuple(
        teyuna_core.MapHex(
            q=q, r=r, type=hex_types[(q, r)], number=number_by_coord[(q, r)]
        )
        for (q, r) in coords
    )


def _neighbor_coordinates(q: int, r: int) -> Iterator[tuple[int, int]]:
    for d in range(6):
        dq, dr = teyuna_core.delta_to_neighbor(d)
        yield q + dq, r + dr


def _reds_are_separated(number_by_coord: dict[tuple[int, int], int]) -> bool:
    for (q, r), number in number_by_coord.items():
        if number not in _RED_NUMBERS:
            continue
        for neighbor in _neighbor_coordinates(q, r):
            if number_by_coord.get(neighbor) in _RED_NUMBERS:
                return False
    return True


def _resolve_board(
    params: teyuna_core.CreateGameRequest,
) -> tuple[
    tuple[teyuna_core.MapHex, ...],
    teyuna_core.HexLocation,
    tuple[teyuna_core.HarbourPair, ...],
]:
    if params.map is None:
        board = generate_map()
    else:
        board = tuple(
            teyuna_core.MapHex(
                q=tile.coordinate.q,
                r=tile.coordinate.r,
                type=tile.type,
                number=tile.number if tile.number is not None else 7,
            )
            for tile in params.map
        )

    if params.harbours is None:
        harbours = teyuna_core.default_harbour_pairs()
    else:
        harbours = teyuna_core.harbour_pairs_from_ports(params.harbours)

    if params.conquistator_location is not None:
        return (
            board,
            teyuna_core.HexLocation(
                q=params.conquistator_location.q, r=params.conquistator_location.r
            ),
            harbours,
        )

    deserts = [hex for hex in board if hex.type == teyuna_core.HexType.DESERT]
    if deserts:
        desert = random.choice(deserts)
        return board, teyuna_core.HexLocation(q=desert.q, r=desert.r), harbours
    if board:
        first = board[0]
        return board, teyuna_core.HexLocation(q=first.q, r=first.r), harbours
    return board, teyuna_core.HexLocation(q=0, r=0), harbours


_TYPES = (
    [teyuna_core.HexType.MOUNTAINS] * 3
    + [teyuna_core.HexType.QUARRIES] * 3
    + [teyuna_core.HexType.HIGHLANDS] * 4
    + [teyuna_core.HexType.VALLEYS] * 4
    + [teyuna_core.HexType.JUNGLE] * 4
    + [teyuna_core.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
_RED_NUMBERS: Final[frozenset[int]] = frozenset({6, 8})
_MAX_MAP_ATTEMPTS: Final[int] = 1000
