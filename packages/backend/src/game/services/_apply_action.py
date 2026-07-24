import datetime
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
        action: teyuna_core.PlayerAction,
    ) -> teyuna_core.ActionExecutionResult: ...

    def timeout_for(self, phase: teyuna_core.GamePhaseName) -> actions.PhaseTimeout: ...


class ApplyActionLocks(Protocol):
    def lock_for(self, game_id: uuid.UUID): ...


class Broker(Protocol):
    async def publish(
        self, game_id: uuid.UUID, data: teyuna_core.ActionExecutionResult
    ) -> None: ...


async def apply_player_action(
    game_id: uuid.UUID,
    action: teyuna_core.PlayerAction,
    *,
    repository: _add_player.UpdateGameRepository,
    registry: ApplyActionRegistry,
    game_locks: ApplyActionLocks,
    broker: Broker,
    now: datetime.datetime | None = None,
) -> tuple[teyuna_core.ActionExecutionResult, entities.Game]:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        game = repository.retrieve(game_id)
        before_phase = game.phase
        result = registry.execute(game, action)
        if before_phase is not game.phase:
            if game.phase is teyuna_core.GamePhaseName.END_GAME:
                game.phase_deadline = None
            else:
                game.phase_deadline = now + registry.timeout_for(game.phase).duration
        repository.update(game_id, game)
    await broker.publish(game_id, result)
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
) -> teyuna_core.ActionExecutionResult | None:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        game = repository.retrieve(game_id)
        if game.phase_deadline is None or now < game.phase_deadline:
            return None

        before_phase = game.phase
        timeout = registry.timeout_for(game.phase)
        action = timeout.on_timeout(game, rng)
        result = registry.execute(game, action)
        if before_phase is not game.phase:
            if game.phase is teyuna_core.GamePhaseName.END_GAME:
                game.phase_deadline = None
            else:
                game.phase_deadline = now + registry.timeout_for(game.phase).duration
        repository.update(game_id, game)

    await broker.publish(game_id, result)
    return result
