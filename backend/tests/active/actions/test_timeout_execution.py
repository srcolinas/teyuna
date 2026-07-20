import collections
import datetime
import random
import uuid
from collections.abc import Callable

import pytest

from src.active import (
    actions,
    entities,
    locks,
    repository as repository_module,
    services,
)
from src.active.actions import timeouts

ZERO = datetime.timedelta(0)
NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def test_zero_timeout_executes_first_placement() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=actions.GamePhaseName.FIRST_PLACEMENT
    )
    game = repository.retrieve(game_id).game
    active = game.active_player

    _apply_due(game_id, repository, registry)

    stored = repository.retrieve(game_id)
    assert len(list(stored.game.players[active].settlements.locations())) == 1
    assert len(stored.game.players[active].paths) == 1


def test_zero_timeout_executes_second_placement() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=actions.GamePhaseName.SECOND_PLACEMENT
    )
    game = repository.retrieve(game_id).game
    active = game.active_player

    _apply_due(game_id, repository, registry)

    stored = repository.retrieve(game_id)
    assert len(list(stored.game.players[active].settlements.locations())) == 1
    assert len(stored.game.players[active].paths) == 1


def test_zero_timeout_executes_dice_roll() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=actions.GamePhaseName.DICE_ROLL
    )

    _apply_due(game_id, repository, registry)

    assert repository.retrieve(game_id).phase is not actions.GamePhaseName.DICE_ROLL


def test_zero_timeout_executes_trade_and_build() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=actions.GamePhaseName.TRADE_AND_BUILD
    )
    active = repository.retrieve(game_id).game.active_player

    _apply_due(game_id, repository, registry)

    stored = repository.retrieve(game_id)
    assert stored.phase is actions.GamePhaseName.DICE_ROLL
    assert stored.game.active_player != active


def test_zero_timeout_executes_discard_resources() -> None:
    def setup(game: entities.ActiveGame) -> None:
        nick = game.active_player
        game.players[nick].resources = collections.Counter(
            {
                entities.ResourceCard.WOOD: 5,
                entities.ResourceCard.GOLD: 4,
            }
        )
        game.to_discard_resources = {nick: 4}

    game_id, repository, registry = _create_stored_game(
        phase=actions.GamePhaseName.DISCARD_RESOURCES,
        setup=setup,
    )
    nick = repository.retrieve(game_id).game.active_player

    _apply_due(game_id, repository, registry)

    stored = repository.retrieve(game_id)
    assert nick not in stored.game.to_discard_resources
    assert stored.phase is actions.GamePhaseName.MOVE_CONQUISTATOR


def test_zero_timeout_executes_move_conquistator() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=actions.GamePhaseName.MOVE_CONQUISTATOR
    )
    before = repository.retrieve(game_id).game.conquistator_location

    _apply_due(game_id, repository, registry)

    stored = repository.retrieve(game_id)
    assert stored.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert stored.game.conquistator_location != before


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (actions.GamePhaseName.DICE_PLAY_WARRIOR, actions.GamePhaseName.DICE_ROLL),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
            actions.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_zero_timeout_executes_play_warrior(
    phase: actions.GamePhaseName,
    expected_phase: actions.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)
    before = repository.retrieve(game_id).game.conquistator_location

    _apply_due(game_id, repository, registry)

    stored = repository.retrieve(game_id)
    assert stored.phase is expected_phase
    assert stored.game.conquistator_location != before


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (actions.GamePhaseName.DICE_PLAY_MAMO, actions.GamePhaseName.DICE_ROLL),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
            actions.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_zero_timeout_executes_play_mamo(
    phase: actions.GamePhaseName,
    expected_phase: actions.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)

    _apply_due(game_id, repository, registry)

    assert repository.retrieve(game_id).phase is expected_phase


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (actions.GamePhaseName.DICE_PLAY_BLESSED, actions.GamePhaseName.DICE_ROLL),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
            actions.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_zero_timeout_executes_play_blessed(
    phase: actions.GamePhaseName,
    expected_phase: actions.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)
    before_supply = sum(repository.retrieve(game_id).game.resource_supply.values())

    _apply_due(game_id, repository, registry)

    stored = repository.retrieve(game_id)
    assert stored.phase is expected_phase
    assert sum(stored.game.resource_supply.values()) == before_supply - 2


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (actions.GamePhaseName.DICE_PLAY_PATHFINDER, actions.GamePhaseName.DICE_ROLL),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
            actions.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_zero_timeout_executes_play_pathfinder(
    phase: actions.GamePhaseName,
    expected_phase: actions.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)

    _apply_due(game_id, repository, registry)

    assert repository.retrieve(game_id).phase is expected_phase


def _zero_timeout_registry() -> actions.ActionsRegistry:
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(
        actions.handle_first_placement
    )
    registry.register(actions.GamePhaseName.SECOND_PLACEMENT)(
        actions.handle_second_placement
    )
    registry.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.register(actions.GamePhaseName.DISCARD_RESOURCES)(
        actions.handle_discard_resources
    )
    registry.register(actions.GamePhaseName.DICE_PLAY_WARRIOR)(
        actions.handle_dice_play_warrior
    )
    registry.register(actions.GamePhaseName.DICE_PLAY_MAMO)(
        actions.handle_dice_play_mamo
    )
    registry.register(actions.GamePhaseName.DICE_PLAY_BLESSED)(
        actions.handle_dice_play_blessed
    )
    registry.register(actions.GamePhaseName.DICE_PLAY_PATHFINDER)(
        actions.handle_dice_play_pathfinder
    )
    registry.register(actions.GamePhaseName.MOVE_CONQUISTATOR)(
        actions.handle_move_conquistator
    )
    registry.register(actions.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    registry.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR)(
        actions.handle_move_conquistator
    )
    registry.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO)(
        actions.handle_trade_and_build_play_mamo
    )
    registry.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED)(
        actions.handle_trade_and_build_play_blessed
    )
    registry.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER)(
        actions.handle_trade_and_build_play_pathfinder
    )

    for phase, on_timeout in (
        (actions.GamePhaseName.FIRST_PLACEMENT, timeouts.timeout_first_placement),
        (actions.GamePhaseName.SECOND_PLACEMENT, timeouts.timeout_second_placement),
        (actions.GamePhaseName.DICE_ROLL, timeouts.timeout_dice_roll),
        (actions.GamePhaseName.DISCARD_RESOURCES, timeouts.timeout_discard_resources),
        (actions.GamePhaseName.MOVE_CONQUISTATOR, timeouts.timeout_move_conquistator),
        (actions.GamePhaseName.DICE_PLAY_WARRIOR, timeouts.timeout_move_conquistator),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
            timeouts.timeout_move_conquistator,
        ),
        (actions.GamePhaseName.DICE_PLAY_MAMO, timeouts.timeout_play_mamo),
        (actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO, timeouts.timeout_play_mamo),
        (actions.GamePhaseName.DICE_PLAY_BLESSED, timeouts.timeout_play_blessed),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
            timeouts.timeout_play_blessed,
        ),
        (actions.GamePhaseName.DICE_PLAY_PATHFINDER, timeouts.timeout_play_pathfinder),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
            timeouts.timeout_play_pathfinder,
        ),
        (actions.GamePhaseName.TRADE_AND_BUILD, timeouts.timeout_trade_and_build),
    ):
        registry.set_timeout(phase, ZERO, on_timeout)

    return registry


def _create_stored_game(
    *,
    phase: actions.GamePhaseName,
    setup: Callable[[entities.ActiveGame], None] | None = None,
) -> tuple[
    uuid.UUID,
    repository_module.InMemoryActiveGameRepository,
    actions.ActionsRegistry,
]:
    repository = repository_module.InMemoryActiveGameRepository()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    game = repository.retrieve(game_id).game
    if setup is not None:
        setup(game)
    repository.update(game_id, game, phase, phase_deadline=NOW)
    return game_id, repository, _zero_timeout_registry()


def _apply_due(
    game_id: uuid.UUID,
    repository: repository_module.InMemoryActiveGameRepository,
    registry: actions.ActionsRegistry,
    *,
    rng: random.Random | None = None,
) -> None:
    services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        rng=rng or random.Random(0),
        now=NOW,
    )
