import datetime
import random
import uuid

import pytest

import teyuna_core

from src.game import (
    actions,
    broker as broker_module,
    entities,
    locks,
    repository as repository_module,
    services,
)
from src.game.actions import _registry

NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


class RecordingBroker:
    def __init__(self) -> None:
        self.events: list[teyuna_core.AnyGameEvent] = []

    async def publish(self, game_id: uuid.UUID, data: teyuna_core.AnyGameEvent) -> None:
        self.events.append(data)


@pytest.mark.asyncio
async def test_apply_player_action_to_end_game_clears_phase_deadline() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={"only": entities.Player()},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        available_slots=0,
        phase=teyuna_core.GamePhaseName.LOBBY,
        phase_deadline=NOW,
    )
    game_id = repository.add(game)
    registry = _lobby_end_game_registry()
    broker = RecordingBroker()

    result, updated = await services.apply_player_action(
        game_id,
        actions.ExecutionContext(
            by="only",
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        teyuna_core.PlayerAction(),
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker,
        now=NOW,
    )

    assert result.error is None
    assert updated.phase is teyuna_core.GamePhaseName.END_GAME
    assert updated.phase_deadline is None
    assert [event.type for event in broker.events] == [
        "successful_action",
        "phase_changed",
        "end_game",
    ]
    end_game = broker.events[-1]
    assert isinstance(end_game, teyuna_core.EndGameEvent)
    assert end_game.winner == "only"
    assert end_game.reason == "victory"


@pytest.mark.asyncio
async def test_apply_player_action_keeps_deadline_when_staying_in_phase() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={nickname: entities.Player() for nickname in ("player-0", "player-1")},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        available_slots=0,
        phase=teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=NOW,
    )
    game.start(datetime.timedelta(seconds=60))
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = NOW
    game_id = repository.add(game)
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        actions.timeouts.timeout_dice_roll,
    )
    broker = RecordingBroker()

    result, updated = await services.apply_player_action(
        game_id,
        actions.ExecutionContext(
            by=game.active_player,
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        teyuna_core.PlayerAction(),
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker,
        now=NOW,
    )

    assert result.error is None
    assert updated.phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert updated.phase_deadline == NOW + datetime.timedelta(seconds=30)
    assert [event.type for event in broker.events] == [
        "successful_action",
        "phase_changed",
        "turn_changed",
    ]


@pytest.mark.asyncio
async def test_apply_timeout_if_due_lobby_timeout_ends_game_and_clears_deadline() -> (
    None
):
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        available_slots=3,
        phase=teyuna_core.GamePhaseName.LOBBY,
        phase_deadline=NOW - datetime.timedelta(seconds=1),
    )
    game_id = repository.add(game)
    registry = _lobby_end_game_registry()
    broker = RecordingBroker()

    result = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker,
        rng=random.Random(0),
        now=NOW,
    )

    assert result is not None
    assert result.error is None
    stored = repository.retrieve(game_id)
    assert stored.phase is teyuna_core.GamePhaseName.END_GAME
    assert stored.phase_deadline is None
    assert [event.type for event in broker.events] == [
        "successful_action",
        "phase_changed",
        "end_game",
    ]
    end_game = broker.events[-1]
    assert isinstance(end_game, teyuna_core.EndGameEvent)
    assert end_game.winner is None
    assert end_game.reason == "lobby_timeout"


@pytest.mark.asyncio
async def test_apply_timeout_if_due_returns_none_when_not_due() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        available_slots=3,
        phase=teyuna_core.GamePhaseName.LOBBY,
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
    assert repository.retrieve(game_id).phase is teyuna_core.GamePhaseName.LOBBY


@pytest.mark.asyncio
async def test_failed_handler_result_publishes_only_failed_action() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={"only": entities.Player()},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        phase=teyuna_core.GamePhaseName.FIRST_PLACEMENT,
    )
    game._turn_order = ["only"]
    game_id = repository.add(game)
    action = teyuna_core.PlayerAction()

    def _failing_handler(
        game: entities.Game,
        context: actions.ExecutionContext,
        action: teyuna_core.PlayerAction,
    ) -> teyuna_core.AnyActionExecutionResult:
        return teyuna_core.ActionExecutionResult(
            previous_phase=game.phase,
            next_phase=game.phase,
            action=action,
            error="action failed",
        )

    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(_failing_handler)
    broker = RecordingBroker()

    result, _ = await services.apply_player_action(
        game_id,
        actions.ExecutionContext(
            by="only",
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        action,
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker,
        now=NOW,
    )

    assert result.error == "action failed"
    assert broker.events == [
        teyuna_core.FailedActionEvent(
            by="only",
            due_to_timeout=False,
            action=action,
            error="action failed",
        )
    ]


@pytest.mark.asyncio
async def test_registry_exception_publishes_failure_and_is_reraised() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={"only": entities.Player()},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        phase=teyuna_core.GamePhaseName.FIRST_PLACEMENT,
    )
    game._turn_order = ["only"]
    game_id = repository.add(game)
    broker = RecordingBroker()
    action = teyuna_core.PlayerAction()

    with pytest.raises(actions.GamePhaseHanlderNotImplementedError) as exc_info:
        await services.apply_player_action(
            game_id,
            actions.ExecutionContext(
                by="only",
                due_to_timeout=False,
                rng=random.Random(0),
            ),
            action,
            repository=repository,
            registry=actions.ActionsRegistry(),
            game_locks=locks.GameLockManager(),
            broker=broker,
            now=NOW,
        )

    assert broker.events == [
        teyuna_core.FailedActionEvent(
            by="only",
            due_to_timeout=False,
            action=action,
            error=str(exc_info.value),
        )
    ]


@pytest.mark.asyncio
async def test_timeout_registry_exception_publishes_timeout_failure() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={"only": entities.Player()},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        phase=teyuna_core.GamePhaseName.FIRST_PLACEMENT,
        phase_deadline=NOW,
    )
    game._turn_order = ["only"]
    game_id = repository.add(game)
    registry = actions.ActionsRegistry()

    def timeout_action(
        game: entities.Game, rng: random.Random
    ) -> _registry.TimeoutAction:
        return _registry.TimeoutAction(by="only", action=teyuna_core.PlayerAction())

    registry.set_timeout(
        teyuna_core.GamePhaseName.FIRST_PLACEMENT,
        datetime.timedelta(seconds=0),
        timeout_action,
    )
    broker = RecordingBroker()

    with pytest.raises(actions.GamePhaseHanlderNotImplementedError):
        await services.apply_timeout_if_due(
            game_id,
            repository=repository,
            registry=registry,
            game_locks=locks.GameLockManager(),
            broker=broker,
            rng=random.Random(0),
            now=NOW,
        )

    assert len(broker.events) == 1
    failure = broker.events[0]
    assert isinstance(failure, teyuna_core.FailedActionEvent)
    assert failure.by == "only"
    assert failure.due_to_timeout is True
    assert failure.action.kind == "advance"


@pytest.mark.asyncio
async def test_transition_events_have_deterministic_order() -> None:
    repository = repository_module.InMemoryGameRepository()
    game = entities.Game(
        map=(),
        players={
            "player-0": entities.Player(),
            "player-1": entities.Player(),
        },
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        phase=teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=NOW,
    )
    game._turn_order = ["player-0", "player-1"]
    game_id = repository.add(game)
    registry = actions.ActionsRegistry()

    def transition(
        game: entities.Game,
        context: actions.ExecutionContext,
        action: teyuna_core.PlayerAction,
    ) -> teyuna_core.ActionExecutionResult:
        previous_phase = game.phase
        game.player_idx = 1
        game.biggest_army = ("player-0", 3)
        game.longest_road = ("player-0", 5)
        game.phase = teyuna_core.GamePhaseName.END_GAME
        return teyuna_core.ActionExecutionResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
        )

    registry.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(transition)
    broker = RecordingBroker()

    await services.apply_player_action(
        game_id,
        actions.ExecutionContext(
            by="player-0",
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        teyuna_core.PlayerAction(),
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=broker,
        now=NOW,
    )

    assert [event.type for event in broker.events] == [
        "successful_action",
        "phase_changed",
        "turn_changed",
        "biggest_army_changed",
        "longest_road_changed",
        "end_game",
    ]
    army = broker.events[3]
    assert isinstance(army, teyuna_core.BiggestArmyChangedEvent)
    assert (army.previous_size, army.current_size) == (0, 3)


def _lobby_end_game_registry() -> actions.ActionsRegistry:
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.LOBBY)(actions.handle_lobby_timeout)
    registry.set_timeout(
        teyuna_core.GamePhaseName.LOBBY,
        datetime.timedelta(seconds=0),
        actions.timeouts.timeout_lobby,
    )
    return registry
