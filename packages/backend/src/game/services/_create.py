import datetime
import random
import uuid
from typing import Protocol

import teyuna_shared

from .. import entities
from . import _retrieve


class CreateGameRepository(_retrieve.RetrieveGameRepository, Protocol):
    def add(
        self,
        game: entities.Game,
    ) -> uuid.UUID: ...


def create_game(
    params: teyuna_shared.CreateGameRequest,
    repository: CreateGameRepository,
    *,
    lobby_timeout: datetime.timedelta,
    now: datetime.datetime | None = None,
) -> teyuna_shared.Game:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)
    board, conquistator = _resolve_board(params)
    game = entities.Game(
        map=board,
        conquistator_location=conquistator,
        players={},
        available_slots=params.num_players,
        phase=teyuna_shared.GamePhaseName.LOBBY,
        phase_deadline=now + lobby_timeout,
    )
    game_id = repository.add(game)
    return _retrieve.retrieve_game(game_id, repository=repository)


def generate_map() -> tuple[teyuna_shared.MapHex, ...]:
    types = list(_TYPES)
    numbers = list(_NUMBERS)
    random.shuffle(types)
    random.shuffle(numbers)

    tiles = []
    type_idx = -1
    number_idx = -1
    for q in range(-2, 3):
        for r in range(-2, 3):
            if (q, r) in teyuna_shared.INVALID_HEX_COORDINATES:
                continue
            type_idx += 1
            hex_type = types[type_idx]
            if hex_type is teyuna_shared.HexType.DESERT:
                number = 7
            else:
                number_idx += 1
                number = numbers[number_idx]
            tiles.append(
                teyuna_shared.MapHex(
                    q=q,
                    r=r,
                    type=hex_type,
                    number=number,
                )
            )

    return tuple(tiles)


def _resolve_board(
    params: teyuna_shared.CreateGameRequest,
) -> tuple[tuple[teyuna_shared.MapHex, ...], teyuna_shared.HexLocation]:
    if params.map is None:
        board = generate_map()
    else:
        board = tuple(
            teyuna_shared.MapHex(
                q=tile.coordinate.q,
                r=tile.coordinate.r,
                type=tile.type,
                number=tile.number if tile.number is not None else 7,
            )
            for tile in params.map
        )

    if params.conquistator_location is not None:
        return board, teyuna_shared.HexLocation(
            q=params.conquistator_location.q, r=params.conquistator_location.r
        )

    deserts = [hex for hex in board if hex.type == teyuna_shared.HexType.DESERT]
    if deserts:
        desert = random.choice(deserts)
        return board, teyuna_shared.HexLocation(q=desert.q, r=desert.r)
    if board:
        first = board[0]
        return board, teyuna_shared.HexLocation(q=first.q, r=first.r)
    return board, teyuna_shared.HexLocation(q=0, r=0)


_TYPES = (
    [teyuna_shared.HexType.MOUNTAINS] * 3
    + [teyuna_shared.HexType.QUARRIES] * 3
    + [teyuna_shared.HexType.HIGHLANDS] * 4
    + [teyuna_shared.HexType.VALLEYS] * 4
    + [teyuna_shared.HexType.JUNGLE] * 4
    + [teyuna_shared.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
