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


@pytest.fixture
def service() -> player.PlayerAuthenticationService:
    return player.PlayerAuthenticationService()
