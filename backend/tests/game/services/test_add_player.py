import datetime

import pytest

from src.game import entities, player, repository as repository_module, services


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
    assert game.phase is entities.GamePhaseName.LOBBY
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

    assert game.phase is entities.GamePhaseName.FIRST_PLACEMENT
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


def test_add_player_reauthenticates_existing_player_without_adding_a_duplicate() -> (
    None
):
    repository = repository_module.InMemoryGameRepository()
    game_id = repository.add(_lobby_game(available_slots=3))
    auth = player.PlayerAuthenticationService()
    game, first_token = services.add_player(
        game_id=game_id,
        nickname="srcolinas",
        repository=repository,
        auth=auth,
        first_placement_timeout=datetime.timedelta(seconds=60),
    )

    game, second_token = services.add_player(
        game_id=game_id,
        nickname="srcolinas",
        repository=repository,
        auth=auth,
        first_placement_timeout=datetime.timedelta(seconds=60),
    )

    assert second_token != first_token
    assert auth.retrieve(second_token) == "srcolinas"
    assert game.available_slots == 2
    assert [p.nickname for p in game.players] == ["srcolinas"]


def _lobby_game(*, available_slots: int) -> entities.Game:
    board = services.generate_map()
    desert = next(h for h in board if h.type is entities.HexType.DESERT)
    return entities.Game(
        map=board,
        conquistator_location=entities.HexLocation(q=desert.q, r=desert.r),
        players={},
        available_slots=available_slots,
        phase=entities.GamePhaseName.LOBBY,
        phase_deadline=datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(minutes=10),
    )
