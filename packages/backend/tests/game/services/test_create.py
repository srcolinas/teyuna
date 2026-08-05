import collections
import datetime

import teyuna_core

from src.game import repository as repository_module, services

_RED_NUMBERS = frozenset({6, 8})
_EXPECTED_NUMBERS = collections.Counter([2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2 + [7])


def test_generate_map_keeps_red_numbers_separated() -> None:
    for _ in range(200):
        board = services.generate_map()
        number_by_coord = {(hex_.q, hex_.r): hex_.number for hex_ in board}

        assert collections.Counter(number_by_coord.values()) == _EXPECTED_NUMBERS

        for (q, r), number in number_by_coord.items():
            if number not in _RED_NUMBERS:
                continue
            for d in range(6):
                dq, dr = teyuna_core.delta_to_neighbor(d)
                neighbor_number = number_by_coord.get((q + dq, r + dr))
                assert neighbor_number not in _RED_NUMBERS


def test_create_game_generates_random_map_when_none_given() -> None:
    repository = repository_module.InMemoryGameRepository()

    game = services.create_game(
        teyuna_core.CreateGameRequest(num_players=3),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert len(game.map) == 19
    assert game.phase is teyuna_core.GamePhaseName.LOBBY
    assert game.available_slots == 3


def test_create_game_places_conquistator_on_desert_when_present() -> None:
    repository = repository_module.InMemoryGameRepository()
    board = _port_map(
        (0, 0, teyuna_core.HexType.DESERT, 7),
        (1, 0, teyuna_core.HexType.MOUNTAINS, 6),
    )

    game = services.create_game(
        teyuna_core.CreateGameRequest(num_players=3, map=board),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.conquistator_location == teyuna_core.HexLocation(q=0, r=0)


def test_create_game_places_conquistator_on_first_hex_when_no_desert() -> None:
    repository = repository_module.InMemoryGameRepository()
    board = _port_map(
        (1, -1, teyuna_core.HexType.MOUNTAINS, 6),
        (0, 1, teyuna_core.HexType.JUNGLE, 5),
    )

    game = services.create_game(
        teyuna_core.CreateGameRequest(num_players=3, map=board),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.conquistator_location == teyuna_core.HexLocation(q=1, r=-1)


def test_create_game_places_conquistator_at_origin_when_map_is_empty() -> None:
    repository = repository_module.InMemoryGameRepository()

    game = services.create_game(
        teyuna_core.CreateGameRequest(num_players=3, map=()),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.map == ()
    assert game.conquistator_location == teyuna_core.HexLocation(q=0, r=0)


def test_create_game_uses_explicit_conquistator_location() -> None:
    repository = repository_module.InMemoryGameRepository()
    board = _port_map(
        (0, 0, teyuna_core.HexType.DESERT, 7),
        (1, 0, teyuna_core.HexType.MOUNTAINS, 6),
    )

    game = services.create_game(
        teyuna_core.CreateGameRequest(
            num_players=3,
            map=board,
            conquistator_location=teyuna_core.HexLocation(q=1, r=0),
        ),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.conquistator_location == teyuna_core.HexLocation(q=1, r=0)


def test_create_game_uses_explicit_harbours() -> None:
    repository = repository_module.InMemoryGameRepository()
    board = _port_map((0, 0, teyuna_core.HexType.DESERT, 7))
    harbour = teyuna_core.Harbour(
        resource=teyuna_core.ResourceCard.GOLD,
        vertices=(
            teyuna_core.Coordinate(q=0, r=0, d=0),
            teyuna_core.Coordinate(q=0, r=0, d=1),
        ),
    )

    game = services.create_game(
        teyuna_core.CreateGameRequest(
            num_players=3,
            map=board,
            conquistator_location=teyuna_core.HexLocation(q=0, r=0),
            harbours=(harbour,),
        ),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.harbours == teyuna_core.grouped_harbours(
        teyuna_core.harbour_pairs_from_ports((harbour,))
    )


def test_create_game_includes_default_harbours() -> None:
    repository = repository_module.InMemoryGameRepository()

    game = services.create_game(
        teyuna_core.CreateGameRequest(num_players=3),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.harbours == teyuna_core.grouped_harbours()


def _port_map(
    *hexes: tuple[int, int, teyuna_core.HexType, int],
) -> tuple[teyuna_core.Hex, ...]:
    return tuple(
        teyuna_core.Hex(
            coordinate=teyuna_core.HexLocation(q=q, r=r),
            type=hex_type,
            number=number,
        )
        for q, r, hex_type, number in hexes
    )
