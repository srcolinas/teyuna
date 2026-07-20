import datetime
import random
import uuid
from typing import Protocol

from .. import actions, entities, repository as repository_module


class ApplyActionRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> repository_module.StoredActiveGame: ...

    def update(
        self,
        id: uuid.UUID,
        game: entities.ActiveGame,
        phase: actions.GamePhaseName,
        phase_deadline: datetime.datetime | None,
    ) -> None: ...


class ApplyActionRegistry(Protocol):
    def execute(
        self,
        phase: actions.GamePhaseName,
        game: entities.ActiveGame,
        action: actions.PlayerAction,
    ) -> actions.ActionExecutionResult: ...

    def timeout_for(self, phase: actions.GamePhaseName) -> actions.PhaseTimeout: ...


class ApplyActionLocks(Protocol):
    def lock_for(self, game_id: uuid.UUID): ...


def apply_player_action(
    game_id: uuid.UUID,
    action: actions.PlayerAction,
    *,
    repository: ApplyActionRepository,
    registry: ApplyActionRegistry,
    game_locks: ApplyActionLocks,
    now: datetime.datetime | None = None,
) -> tuple[actions.ActionExecutionResult, entities.ActiveGame]:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        stored = repository.retrieve(game_id)
        result = registry.execute(stored.phase, stored.game, action)
        if result.succeeded:
            deadline = _deadline_for(registry, result.phase, now)
            repository.update(game_id, stored.game, result.phase, deadline)
        return result, stored.game


def apply_timeout_if_due(
    game_id: uuid.UUID,
    *,
    repository: ApplyActionRepository,
    registry: ApplyActionRegistry,
    game_locks: ApplyActionLocks,
    rng: random.Random,
    now: datetime.datetime | None = None,
) -> actions.ActionExecutionResult | None:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        stored = repository.retrieve(game_id)
        if stored.phase_deadline is None or now < stored.phase_deadline:
            return None

        timeout = registry.timeout_for(stored.phase)
        action = timeout.on_timeout(stored.game, rng)
        result = registry.execute(stored.phase, stored.game, action)
        if result.succeeded:
            deadline = _deadline_for(registry, result.phase, now)
            repository.update(game_id, stored.game, result.phase, deadline)
        return result


def _deadline_for(
    registry: ApplyActionRegistry,
    phase: actions.GamePhaseName,
    now: datetime.datetime,
) -> datetime.datetime | None:
    try:
        timeout = registry.timeout_for(phase)
    except KeyError:
        return None
    return now + timeout.duration
