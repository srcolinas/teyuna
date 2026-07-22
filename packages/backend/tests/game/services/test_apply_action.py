import datetime
import random

import pytest

from src.game import (
    actions,
    broker as broker_module,
    entities,
    locks,
    repository as repository_module,
    services,
)

NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


@pytest.mark.asyncio
async def test_apply_player_action_to_end_game_clears_phase_deadline() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={"only": entities.Player()},
        conquistator_location=entities.HexLocation(q=0, r=0),
        available_slots=0,
        phase=entities.GamePhaseName.LOBBY,
        phase_deadline=NOW,
    )
    game_id = repository.add(game)
    registry = _lobby_end_game_registry()

    result, updated = await services.apply_player_action(
        game_id,
        actions.PlayerAction(by="only"),
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker_module.EventBroker(),
        now=NOW,
    )

    assert result.error is None
    assert updated.phase is entities.GamePhaseName.END_GAME
    assert updated.phase_deadline is None


@pytest.mark.asyncio
async def test_apply_player_action_keeps_deadline_when_staying_in_phase() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={nickname: entities.Player() for nickname in ("player-0", "player-1")},
        conquistator_location=entities.HexLocation(q=0, r=0),
        available_slots=0,
        phase=entities.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=NOW,
    )
    game.start(datetime.timedelta(seconds=60))
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = NOW
    game_id = repository.add(game)
    registry = actions.ActionsRegistry()
    registry.register(entities.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    registry.set_timeout(
        entities.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        actions.timeouts.timeout_dice_roll,
    )

    result, updated = await services.apply_player_action(
        game_id,
        actions.PlayerAction(by=game.active_player),
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker_module.EventBroker(),
        now=NOW,
    )

    assert result.error is None
    assert updated.phase is entities.GamePhaseName.DICE_ROLL
    assert updated.phase_deadline == NOW + datetime.timedelta(seconds=30)


@pytest.mark.asyncio
async def test_apply_timeout_if_due_lobby_timeout_ends_game_and_clears_deadline() -> (
    None
):
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={},
        conquistator_location=entities.HexLocation(q=0, r=0),
        available_slots=3,
        phase=entities.GamePhaseName.LOBBY,
        phase_deadline=NOW - datetime.timedelta(seconds=1),
    )
    game_id = repository.add(game)
    registry = _lobby_end_game_registry()

    result = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker_module.EventBroker(),
        rng=random.Random(0),
        now=NOW,
    )

    assert result is not None
    assert result.error is None
    stored = repository.retrieve(game_id)
    assert stored.phase is entities.GamePhaseName.END_GAME
    assert stored.phase_deadline is None


@pytest.mark.asyncio
async def test_apply_timeout_if_due_returns_none_when_not_due() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={},
        conquistator_location=entities.HexLocation(q=0, r=0),
        available_slots=3,
        phase=entities.GamePhaseName.LOBBY,
        phase_deadline=NOW + datetime.timedelta(minutes=10),
    )
    game_id = repository.add(game)
    registry = _lobby_end_game_registry()

    result = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker_module.EventBroker(),
        rng=random.Random(0),
        now=NOW,
    )

    assert result is None
    assert repository.retrieve(game_id).phase is entities.GamePhaseName.LOBBY


def _lobby_end_game_registry() -> actions.ActionsRegistry:
    registry = actions.ActionsRegistry()
    registry.register(entities.GamePhaseName.LOBBY)(actions.handle_lobby_timeout)
    registry.set_timeout(
        entities.GamePhaseName.LOBBY,
        datetime.timedelta(seconds=0),
        actions.timeouts.timeout_lobby,
    )
    return registry
