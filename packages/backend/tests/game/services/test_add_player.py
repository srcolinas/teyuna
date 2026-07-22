import datetime

import pytest

from src.game import entities, player, repository as repository_module, services
import teyuna_shared


def test_add_player_adds_to_lobby_and_returns_token() -> None:
    repository = repository_module.InMemoryGameRepository()
    game_id = repository.add(_lobby_game(available_slots=3))
    auth = player.PlayerAuthenticationService()

    game, token = services.add_player(
        game_id=game_id,
        nickname="srcolinas",
        repository=repository,
        auth=auth,
        first_placement_timeout=datetime.timedelta(seconds=60),
    )

    assert auth.retrieve(token) == "srcolinas"
    assert game.phase is teyuna_shared.GamePhaseName.LOBBY
    assert game.available_slots == 2
    assert {p.nickname for p in game.players} == {"srcolinas"}


def test_add_player_starts_game_when_last_slot_filled() -> None:
    repository = repository_module.InMemoryGameRepository()
    game_id = repository.add(_lobby_game(available_slots=1))
    auth = player.PlayerAuthenticationService()

    game, _ = services.add_player(
        game_id=game_id,
        nickname="srcolinas",
        repository=repository,
        auth=auth,
        first_placement_timeout=datetime.timedelta(seconds=60),
    )

    assert game.phase is teyuna_shared.GamePhaseName.FIRST_PLACEMENT
    assert game.available_slots == 0
    assert game.turn_order == ("srcolinas",)


def test_add_player_raises_when_game_already_started() -> None:
    repository = repository_module.InMemoryGameRepository()
    started = _lobby_game(available_slots=0)
    started.players["already-in"] = entities.Player()
    started.start(datetime.timedelta(seconds=60))
    game_id = repository.add(started)
    auth = player.PlayerAuthenticationService()

    with pytest.raises(services.GameAlreadyStartedError):
        services.add_player(
            game_id=game_id,
            nickname="late",
            repository=repository,
            auth=auth,
            first_placement_timeout=datetime.timedelta(seconds=60),
        )


def test_add_player_raises_when_nickname_already_taken() -> None:
    repository = repository_module.InMemoryGameRepository()
    game_id = repository.add(_lobby_game(available_slots=3))
    auth = player.PlayerAuthenticationService()
    services.add_player(
        game_id=game_id,
        nickname="srcolinas",
        repository=repository,
        auth=auth,
        first_placement_timeout=datetime.timedelta(seconds=60),
    )

    with pytest.raises(entities.NicknameAlreadyTakenError):
        services.add_player(
            game_id=game_id,
            nickname="srcolinas",
            repository=repository,
            auth=auth,
            first_placement_timeout=datetime.timedelta(seconds=60),
        )


def _lobby_game(*, available_slots: int) -> entities.Game:
    board = services.generate_map()
    desert = next(h for h in board if h.type is teyuna_shared.HexType.DESERT)
    return entities.Game(
        map=board,
        conquistator_location=teyuna_shared.HexLocation(q=desert.q, r=desert.r),
        players={},
        available_slots=available_slots,
        phase=teyuna_shared.GamePhaseName.LOBBY,
        phase_deadline=datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(minutes=10),
    )
