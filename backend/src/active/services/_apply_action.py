import datetime
import random
import uuid
from collections.abc import Callable
from typing import TypeVar

from .. import actions, entities, locks, repository as repository_module

BeforeT = TypeVar("BeforeT")


def apply_player_action(
    game_id: uuid.UUID,
    action: actions.PlayerAction,
    *,
    repository: repository_module.InMemoryActiveGameRepository,
    registry: actions.ActionsRegistry,
    game_locks: locks.GameLockManager,
    now: datetime.datetime | None = None,
    before: Callable[[entities.ActiveGame], BeforeT] | None = None,
) -> tuple[actions.GamePhaseName, entities.ActiveGame, BeforeT | None]:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        stored = repository.retrieve(game_id)
        before_value = before(stored.game) if before is not None else None
        new_phase = registry.execute(stored.phase, stored.game, action)
        deadline = _deadline_for(registry, new_phase, now)
        repository.update(game_id, stored.game, new_phase, deadline)
        return new_phase, stored.game, before_value


def apply_timeout_if_due(
    game_id: uuid.UUID,
    *,
    repository: repository_module.InMemoryActiveGameRepository,
    registry: actions.ActionsRegistry,
    game_locks: locks.GameLockManager,
    rng: random.Random,
    now: datetime.datetime | None = None,
) -> None:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)

    with game_locks.lock_for(game_id):
        stored = repository.retrieve(game_id)
        if stored.phase_deadline is None or now < stored.phase_deadline:
            return

        timeout = registry.timeout_for(stored.phase)
        action = timeout.on_timeout(stored.game, rng)
        phase = registry.execute(stored.phase, stored.game, action)
        deadline = _deadline_for(registry, phase, now)
        repository.update(game_id, stored.game, phase, deadline)


def _deadline_for(
    registry: actions.ActionsRegistry,
    phase: actions.GamePhaseName,
    now: datetime.datetime,
) -> datetime.datetime | None:
    try:
        timeout = registry.timeout_for(phase)
    except KeyError:
        return None
    return now + timeout.duration
