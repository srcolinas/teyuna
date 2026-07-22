import datetime
import random
import uuid
from typing import Protocol

from .. import ports, entities
from . import _retrieve


class CreateGameRepository(_retrieve.RetrieveGameRepository, Protocol):
    def add(
        self,
        game: entities.Game,
    ) -> uuid.UUID: ...


def create_game(
    params: ports.CreateGameRequest,
    repository: CreateGameRepository,
    *,
    lobby_timeout: datetime.timedelta,
    now: datetime.datetime | None = None,
) -> ports.Game:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)
    board, conquistator = _resolve_board(params)
    game = entities.Game(
        map=board,
        conquistator_location=conquistator,
        players={},
        available_slots=params.num_players,
        phase=entities.GamePhaseName.LOBBY,
        phase_deadline=now + lobby_timeout,
    )
    game_id = repository.add(game)
    return _retrieve.retrieve_game(game_id, repository=repository)


def generate_map() -> tuple[entities.Hex, ...]:
    types = list(_TYPES)
    numbers = list(_NUMBERS)
    random.shuffle(types)
    random.shuffle(numbers)

    tiles = []
    type_idx = -1
    number_idx = -1
    for q in range(-2, 3):
        for r in range(-2, 3):
            if (q, r) in entities.INVALID_HEX_COORDINATES:
                continue
            type_idx += 1
            hex_type = types[type_idx]
            if hex_type is entities.HexType.DESERT:
                number = 7
            else:
                number_idx += 1
                number = numbers[number_idx]
            tiles.append(
                entities.Hex(
                    q=q,
                    r=r,
                    type=hex_type,
                    number=number,
                )
            )

    return tuple(tiles)


def _resolve_board(
    params: ports.CreateGameRequest,
) -> tuple[tuple[entities.Hex, ...], entities.HexLocation]:
    if params.map is None:
        board = generate_map()
    else:
        board = tuple(
            entities.Hex(
                q=tile.coordinate.q,
                r=tile.coordinate.r,
                type=tile.type,
                number=tile.number if tile.number is not None else 7,
            )
            for tile in params.map
        )

    if params.conquistator_location is not None:
        return board, entities.HexLocation(
            q=params.conquistator_location.q, r=params.conquistator_location.r
        )

    deserts = [hex for hex in board if hex.type == entities.HexType.DESERT]
    if deserts:
        desert = random.choice(deserts)
        return board, entities.HexLocation(q=desert.q, r=desert.r)
    if board:
        first = board[0]
        return board, entities.HexLocation(q=first.q, r=first.r)
    return board, entities.HexLocation(q=0, r=0)


_TYPES = (
    [entities.HexType.MOUNTAINS] * 3
    + [entities.HexType.QUARRIES] * 3
    + [entities.HexType.HIGHLANDS] * 4
    + [entities.HexType.VALLEYS] * 4
    + [entities.HexType.JUNGLE] * 4
    + [entities.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
