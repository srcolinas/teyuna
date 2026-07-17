import uuid

import pytest

from src import player


def test_tokens_are_unique(service: player.PlayerAuthenticationService) -> None:
    trials = 1000
    tokens = set()
    for i in range(trials):
        t = service.add(f"srcolinas-{i}")
        tokens.add(t)
    assert len(tokens) == trials


def test_added_nickname_is_returned_by_token(
    service: player.PlayerAuthenticationService,
) -> None:
    nickname = str(uuid.uuid4())
    token = service.add(nickname)
    assert service.retrieve(token) == nickname


def test_retries_when_token_collides() -> None:
    tokens = iter(["same-token", "same-token", "unique-token"])
    service = player.PlayerAuthenticationService(token_generator=lambda: next(tokens))

    assert service.add("alice") == "same-token"
    assert service.add("bob") == "unique-token"
    assert service.retrieve("unique-token") == "bob"


@pytest.fixture
def service() -> player.PlayerAuthenticationService:
    return player.PlayerAuthenticationService()
