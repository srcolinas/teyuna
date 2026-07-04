from __future__ import annotations

import datetime
import uuid

import pytest

from src import player, proposed


def test_player_can_be_added_before_expiration(
    repository: proposed.InMemoryProposedGameRepository,
    manager: proposed.GameManager,
    auth: player.PlayerAuthenticationService,
) -> None:
    game_id = repository.add(
        num_players=3,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id
    result, _ = proposed.add_player(
        game_id=game_id,
        username="srcolinas",
        repository=repository,
        manager=manager,
        auth=auth,
    )
    assert len(result.proposed.players) == 1
    assert list(result.proposed.players)[0] == "srcolinas"


def test_player_cannot_be_added_after_expiration(
    repository: proposed.InMemoryProposedGameRepository,
    manager: proposed.GameManager,
    auth: player.PlayerAuthenticationService,
) -> None:
    game_id = repository.add(
        num_players=3,
        expires_at=datetime.datetime.now() - datetime.timedelta(seconds=100),
    ).id
    with pytest.raises(proposed.GameExpiredError):
        proposed.add_player(
            game_id=game_id,
            username="srcolinas",
            repository=repository,
            manager=manager,
            auth=auth,
        )


def test_full_game_starts(
    repository: proposed.InMemoryProposedGameRepository,
    manager: FakeManager,
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
            username=p,
            repository=repository,
            manager=manager,
            auth=auth,
        )
    result, _ = proposed.add_player(
        game_id=game_id,
        username=players[-1],
        repository=repository,
        manager=manager,
        auth=auth,
    )

    assert result.game is not None
    assert sorted(manager.memory[result.game]) == sorted(players)


def test_not_full_game_is_not_started(
    repository: proposed.InMemoryProposedGameRepository,
    manager: FakeManager,
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
            username=f"srcolinas-{i}",
            repository=repository,
            manager=manager,
            auth=auth,
        )
        assert result.game is None


@pytest.fixture
def repository() -> proposed.InMemoryProposedGameRepository:
    return proposed.InMemoryProposedGameRepository()


class FakeManager:
    def __init__(self) -> None:
        self.memory: dict[uuid.UUID, tuple[str, ...]] = {}

    def start(self, players: tuple[str, ...]) -> uuid.UUID:
        id = uuid.uuid4()
        self.memory[id] = players
        return id


@pytest.fixture
def manager() -> FakeManager:
    return FakeManager()


@pytest.fixture
def auth() -> player.PlayerAuthenticationService:
    return player.PlayerAuthenticationService()
