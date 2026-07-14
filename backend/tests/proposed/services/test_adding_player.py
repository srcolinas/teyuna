from __future__ import annotations

import datetime

import pytest

from src import active, player, proposed
from src.active import entities
from src.active.services import phases


def test_player_can_be_added_before_expiration(
    repository: proposed.InMemoryProposedGameRepository,
    game_manager: active.services.GameManager,
    auth: player.PlayerAuthenticationService,
) -> None:
    game_id = repository.add(
        num_players=3,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id
    result, _ = proposed.add_player(
        game_id=game_id,
        nickname="srcolinas",
        repository=repository,
        game_manager=game_manager,
        auth=auth,
    )
    assert len(result.proposed.players) == 1
    assert list(result.proposed.players)[0] == "srcolinas"


def test_player_cannot_be_added_after_expiration(
    repository: proposed.InMemoryProposedGameRepository,
    game_manager: active.services.GameManager,
    auth: player.PlayerAuthenticationService,
) -> None:
    game_id = repository.add(
        num_players=3,
        expires_at=datetime.datetime.now() - datetime.timedelta(seconds=100),
    ).id
    with pytest.raises(proposed.GameExpiredError):
        proposed.add_player(
            game_id=game_id,
            nickname="srcolinas",
            repository=repository,
            game_manager=game_manager,
            auth=auth,
        )


def test_full_game_starts(
    repository: proposed.InMemoryProposedGameRepository,
    game_manager: active.services.GameManager,
    auth: player.PlayerAuthenticationService,
) -> None:
    game_id = repository.add(
        num_players=3,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id
    players = ["srcolinas-1", "srcolinas-2", "srcolinas-3"]
    for p in players[:-1]:
        proposed.add_player(
            game_id=game_id,
            nickname=p,
            repository=repository,
            game_manager=game_manager,
            auth=auth,
        )
    result, _ = proposed.add_player(
        game_id=game_id,
        nickname=players[-1],
        repository=repository,
        game_manager=game_manager,
        auth=auth,
    )

    assert result.game is not None
    entity_game = game_manager.retrieve(result.game)
    assert sorted(entity_game.turn_order) == sorted(players)


def test_not_full_game_is_not_started(
    repository: proposed.InMemoryProposedGameRepository,
    game_manager: active.services.GameManager,
    auth: player.PlayerAuthenticationService,
) -> None:
    num_players = 3
    game_id = repository.add(
        num_players=num_players,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id
    for i in range(num_players - 1):
        result, _ = proposed.add_player(
            game_id=game_id,
            nickname=f"srcolinas-{i}",
            repository=repository,
            game_manager=game_manager,
            auth=auth,
        )
        assert result.game is None


@pytest.fixture
def repository() -> proposed.InMemoryProposedGameRepository:
    return proposed.InMemoryProposedGameRepository()


@pytest.fixture
def game_manager() -> active.services.GameManager:
    class FirstNode(phases.GamePhaseNode[None, None, None]):
        def run(
            self, game: entities.ActiveGame, request: phases.PlayerRequest
        ) -> phases.RunOutcome[None]:
            return phases.RunOutcome(finished=False, value=None)

        def on_exit(self, game: entities.ActiveGame) -> phases.ExitOutcome[None]:
            return phases.ExitOutcome(
                next=phases.GamePhaseName.FIRST_PLACEMENT, value=None
            )

        def on_enter(self, game: entities.ActiveGame) -> phases.EnterOutcome[None]:
            return phases.EnterOutcome(value=None)

    return active.services.GameManager(
        {phases.GamePhaseName.FIRST_PLACEMENT: FirstNode()}
    )


@pytest.fixture
def auth() -> player.PlayerAuthenticationService:
    return player.PlayerAuthenticationService()
