import datetime

from src.game import repository as repository_module, services
import teyuna_shared


def test_create_game_generates_random_map_when_none_given() -> None:
    repository = repository_module.InMemoryGameRepository()

    game = services.create_game(
        teyuna_shared.CreateGameRequest(num_players=3),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert len(game.map) == 19
    assert game.phase is teyuna_shared.GamePhaseName.LOBBY
    assert game.available_slots == 3


def test_create_game_places_conquistator_on_desert_when_present() -> None:
    repository = repository_module.InMemoryGameRepository()
    board = _port_map(
        (0, 0, teyuna_shared.HexType.DESERT, 7),
        (1, 0, teyuna_shared.HexType.MOUNTAINS, 6),
    )

    game = services.create_game(
        teyuna_shared.CreateGameRequest(num_players=3, map=board),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.conquistator_location == teyuna_shared.HexCoordinate(q=0, r=0)


def test_create_game_places_conquistator_on_first_hex_when_no_desert() -> None:
    repository = repository_module.InMemoryGameRepository()
    board = _port_map(
        (1, -1, teyuna_shared.HexType.MOUNTAINS, 6),
        (0, 1, teyuna_shared.HexType.JUNGLE, 5),
    )

    game = services.create_game(
        teyuna_shared.CreateGameRequest(num_players=3, map=board),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.conquistator_location == teyuna_shared.HexCoordinate(q=1, r=-1)


def test_create_game_places_conquistator_at_origin_when_map_is_empty() -> None:
    repository = repository_module.InMemoryGameRepository()

    game = services.create_game(
        teyuna_shared.CreateGameRequest(num_players=3, map=()),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.map == ()
    assert game.conquistator_location == teyuna_shared.HexCoordinate(q=0, r=0)


def test_create_game_uses_explicit_conquistator_location() -> None:
    repository = repository_module.InMemoryGameRepository()
    board = _port_map(
        (0, 0, teyuna_shared.HexType.DESERT, 7),
        (1, 0, teyuna_shared.HexType.MOUNTAINS, 6),
    )

    game = services.create_game(
        teyuna_shared.CreateGameRequest(
            num_players=3,
            map=board,
            conquistator_location=teyuna_shared.HexCoordinate(q=1, r=0),
        ),
        repository,
        lobby_timeout=datetime.timedelta(minutes=10),
    )

    assert game.conquistator_location == teyuna_shared.HexCoordinate(q=1, r=0)


def _port_map(
    *hexes: tuple[int, int, teyuna_shared.HexType, int],
) -> tuple[teyuna_shared.Hex, ...]:
    return tuple(
        teyuna_shared.Hex(
            coordinate=teyuna_shared.HexCoordinate(q=q, r=r),
            type=hex_type,
            number=number,
        )
        for q, r, hex_type, number in hexes
    )
