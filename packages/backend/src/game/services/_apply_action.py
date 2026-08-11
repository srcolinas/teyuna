import datetime
import dataclasses
import random
import uuid
from typing import Protocol

import teyuna_core

from .. import entities, actions
from . import _add_player


class ApplyActionRegistry(Protocol):
    def execute(
        self,
        game: entities.Game,
        context: actions.ExecutionContext,
        action: teyuna_core.AnyPlayerAction,
    ) -> teyuna_core.AnyActionExecutionResult: ...

    def timeout_for(self, phase: teyuna_core.GamePhaseName) -> actions.PhaseTimeout: ...


class ApplyActionLocks(Protocol):
    def lock_for(self, game_id: uuid.UUID): ...


class Broker(Protocol):
    async def publish(
        self, game_id: uuid.UUID, data: teyuna_core.AnyGameEvent
    ) -> None: ...


@dataclasses.dataclass(frozen=True, slots=True)
class _GameSnapshot:
    phase: teyuna_core.GamePhaseName
    active_player: str | None
    biggest_army: tuple[str | None, int]
    longest_road: tuple[str | None, int]


async def apply_player_action(
    game_id: uuid.UUID,
    context: actions.ExecutionContext,
    action: teyuna_core.AnyPlayerAction,
    *,
    repository: _add_player.UpdateGameRepository,
    registry: ApplyActionRegistry,
    game_locks: ApplyActionLocks,
    broker: Broker,
    now: datetime.datetime | None = None,
) -> tuple[teyuna_core.AnyActionExecutionResult, entities.Game]:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        game = repository.retrieve(game_id)
        before = _snapshot(game)
        execution_error: (
            actions.ActionNotAllowedError
            | actions.GamePhaseHanlderNotImplementedError
            | None
        ) = None
        try:
            result = registry.execute(game, context, action)
        except (
            actions.ActionNotAllowedError,
            actions.GamePhaseHanlderNotImplementedError,
        ) as exc:
            execution_error = exc
        else:
            _update_phase_deadline(game, before.phase, registry, now)
            repository.update(game_id, game)
            after = _snapshot(game)

    if execution_error is not None:
        await _publish_failed_action(
            game_id,
            context,
            action,
            error=str(execution_error),
            broker=broker,
        )
        raise execution_error

    await _publish_events(
        game_id,
        context,
        action,
        result,
        before,
        after,
        broker=broker,
    )
    return result, game


async def apply_timeout_if_due(
    game_id: uuid.UUID,
    *,
    repository: _add_player.UpdateGameRepository,
    registry: ApplyActionRegistry,
    game_locks: ApplyActionLocks,
    broker: Broker,
    rng: random.Random,
    now: datetime.datetime | None = None,
) -> teyuna_core.AnyActionExecutionResult | None:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        game = repository.retrieve(game_id)
        if game.phase_deadline is None or now < game.phase_deadline:
            return None

        before = _snapshot(game)
        timeout = registry.timeout_for(game.phase)
        timeout_action = timeout.on_timeout(game, rng)
        context = actions.ExecutionContext(
            by=timeout_action.by,
            due_to_timeout=True,
            rng=rng,
        )
        execution_error: (
            actions.ActionNotAllowedError
            | actions.GamePhaseHanlderNotImplementedError
            | None
        ) = None
        try:
            result = registry.execute(game, context, timeout_action.action)
        except (
            actions.ActionNotAllowedError,
            actions.GamePhaseHanlderNotImplementedError,
        ) as exc:
            execution_error = exc
        else:
            _update_phase_deadline(game, before.phase, registry, now)
            repository.update(game_id, game)
            after = _snapshot(game)

    if execution_error is not None:
        await _publish_failed_action(
            game_id,
            context,
            timeout_action.action,
            error=str(execution_error),
            broker=broker,
        )
        raise execution_error

    await _publish_events(
        game_id,
        context,
        timeout_action.action,
        result,
        before,
        after,
        broker=broker,
    )
    return result


def _snapshot(game: entities.Game) -> _GameSnapshot:
    return _GameSnapshot(
        phase=game.phase,
        active_player=_active_player(game),
        biggest_army=game.biggest_army,
        longest_road=game.longest_road,
    )


def _active_player(game: entities.Game) -> str | None:
    try:
        return game.active_player
    except IndexError:
        return None


def _update_phase_deadline(
    game: entities.Game,
    previous_phase: teyuna_core.GamePhaseName,
    registry: ApplyActionRegistry,
    now: datetime.datetime,
) -> None:
    if previous_phase is game.phase:
        return
    if game.phase is teyuna_core.GamePhaseName.END_GAME:
        game.phase_deadline = None
    else:
        game.phase_deadline = now + registry.timeout_for(game.phase).duration


async def _publish_failed_action(
    game_id: uuid.UUID,
    context: actions.ExecutionContext,
    action: teyuna_core.AnyPlayerAction,
    *,
    error: str,
    broker: Broker,
) -> None:
    await broker.publish(
        game_id,
        teyuna_core.FailedActionEvent(
            by=context.by,
            due_to_timeout=context.due_to_timeout,
            action=action,
            error=error,
        ),
    )


async def _publish_events(
    game_id: uuid.UUID,
    context: actions.ExecutionContext,
    action: teyuna_core.AnyPlayerAction,
    result: teyuna_core.AnyActionExecutionResult,
    before: _GameSnapshot,
    after: _GameSnapshot,
    *,
    broker: Broker,
) -> None:
    events: list[teyuna_core.AnyGameEvent] = []
    if result.error is not None:
        events.append(
            teyuna_core.FailedActionEvent(
                by=context.by,
                due_to_timeout=context.due_to_timeout,
                action=action,
                error=result.error,
            )
        )
    else:
        events.append(
            teyuna_core.SuccessfulActionEvent(
                by=context.by,
                due_to_timeout=context.due_to_timeout,
                action=action,
                result=result,
            )
        )

    if before.phase is not after.phase:
        events.append(
            teyuna_core.PhaseChangedEvent(
                previous_phase=before.phase,
                next_phase=after.phase,
            )
        )
    if before.active_player != after.active_player:
        events.append(
            teyuna_core.TurnChangedEvent(
                previous_player=before.active_player,
                next_player=after.active_player,
            )
        )
    if before.biggest_army != after.biggest_army:
        events.append(
            teyuna_core.BiggestArmyChangedEvent(
                previous_holder=before.biggest_army[0],
                current_holder=after.biggest_army[0],
                previous_size=before.biggest_army[1],
                current_size=after.biggest_army[1],
            )
        )
    if before.longest_road != after.longest_road:
        events.append(
            teyuna_core.LongestRoadChangedEvent(
                previous_holder=before.longest_road[0],
                current_holder=after.longest_road[0],
                previous_length=before.longest_road[1],
                current_length=after.longest_road[1],
            )
        )
    if (
        before.phase is not teyuna_core.GamePhaseName.END_GAME
        and after.phase is teyuna_core.GamePhaseName.END_GAME
    ):
        lobby_timeout = (
            before.phase is teyuna_core.GamePhaseName.LOBBY and context.due_to_timeout
        )
        events.append(
            teyuna_core.EndGameEvent(
                winner=None if lobby_timeout else context.by,
                reason="lobby_timeout" if lobby_timeout else "victory",
            )
        )

    for event in events:
        await broker.publish(game_id, event)
