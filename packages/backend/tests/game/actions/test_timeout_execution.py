import collections
import datetime
import random
import uuid
from collections.abc import Callable

import pytest

from src.game import (
    actions,
    broker,
    entities,
    locks,
    repository as repository_module,
    services,
)
from src.game.actions import timeouts

ZERO = datetime.timedelta(0)
NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


@pytest.mark.asyncio
async def test_zero_timeout_executes_first_placement() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=entities.GamePhaseName.FIRST_PLACEMENT
    )
    game = repository.retrieve(game_id)
    active = game.active_player
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    stored = repository.retrieve(game_id)
    assert len(list(stored.players[active].settlements.locations())) == 1
    assert len(stored.players[active].paths) == 1


@pytest.mark.asyncio
async def test_zero_timeout_executes_second_placement() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=entities.GamePhaseName.SECOND_PLACEMENT
    )
    game = repository.retrieve(game_id)
    active = game.active_player
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    stored = repository.retrieve(game_id)
    assert len(list(stored.players[active].settlements.locations())) == 1
    assert len(stored.players[active].paths) == 1


@pytest.mark.asyncio
async def test_zero_timeout_executes_dice_roll() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=entities.GamePhaseName.DICE_ROLL
    )
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    assert repository.retrieve(game_id).phase is not entities.GamePhaseName.DICE_ROLL


@pytest.mark.asyncio
async def test_zero_timeout_executes_trade_and_build() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=entities.GamePhaseName.TRADE_AND_BUILD
    )
    active = repository.retrieve(game_id).active_player
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    stored = repository.retrieve(game_id)
    assert stored.phase is entities.GamePhaseName.DICE_ROLL
    assert stored.active_player != active


@pytest.mark.asyncio
async def test_zero_timeout_executes_discard_resources() -> None:
    def setup(game: entities.Game) -> None:
        nick = game.active_player
        game.players[nick].resources = collections.Counter(
            {
                entities.ResourceCard.WOOD: 5,
                entities.ResourceCard.GOLD: 4,
            }
        )
        game.to_discard_resources = {nick: 4}

    game_id, repository, registry = _create_stored_game(
        phase=entities.GamePhaseName.DISCARD_RESOURCES,
        setup=setup,
    )
    nick = repository.retrieve(game_id).active_player
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    stored = repository.retrieve(game_id)
    assert nick not in stored.to_discard_resources
    assert stored.phase is entities.GamePhaseName.MOVE_CONQUISTATOR


@pytest.mark.asyncio
async def test_zero_timeout_executes_move_conquistator() -> None:
    game_id, repository, registry = _create_stored_game(
        phase=entities.GamePhaseName.MOVE_CONQUISTATOR
    )
    before = repository.retrieve(game_id).conquistator_location
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    stored = repository.retrieve(game_id)
    assert stored.phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert stored.conquistator_location != before


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (entities.GamePhaseName.DICE_PLAY_WARRIOR, entities.GamePhaseName.DICE_ROLL),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
            entities.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
@pytest.mark.asyncio
async def test_zero_timeout_executes_play_warrior(
    phase: entities.GamePhaseName,
    expected_phase: entities.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)
    before = repository.retrieve(game_id).conquistator_location
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    stored = repository.retrieve(game_id)
    assert stored.phase is expected_phase
    assert stored.conquistator_location != before


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (entities.GamePhaseName.DICE_PLAY_MAMO, entities.GamePhaseName.DICE_ROLL),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
            entities.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
@pytest.mark.asyncio
async def test_zero_timeout_executes_play_mamo(
    phase: entities.GamePhaseName,
    expected_phase: entities.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    assert repository.retrieve(game_id).phase is expected_phase


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (entities.GamePhaseName.DICE_PLAY_BLESSED, entities.GamePhaseName.DICE_ROLL),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
            entities.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
@pytest.mark.asyncio
async def test_zero_timeout_executes_play_blessed(
    phase: entities.GamePhaseName,
    expected_phase: entities.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)
    before_supply = sum(repository.retrieve(game_id).resource_supply.values())
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    stored = repository.retrieve(game_id)
    assert stored.phase is expected_phase
    assert sum(stored.resource_supply.values()) == before_supply - 2


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        (entities.GamePhaseName.DICE_PLAY_PATHFINDER, entities.GamePhaseName.DICE_ROLL),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
            entities.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
@pytest.mark.asyncio
async def test_zero_timeout_executes_play_pathfinder(
    phase: entities.GamePhaseName,
    expected_phase: entities.GamePhaseName,
) -> None:
    game_id, repository, registry = _create_stored_game(phase=phase)
    event_broker = broker.EventBroker()

    result = await _apply_due(game_id, repository, registry, event_broker=event_broker)

    assert result is not None
    assert result.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1
    assert repository.retrieve(game_id).phase is expected_phase


def _zero_timeout_registry() -> actions.ActionsRegistry:
    registry = actions.ActionsRegistry()
    registry.register(entities.GamePhaseName.FIRST_PLACEMENT)(
        actions.handle_first_placement
    )
    registry.register(entities.GamePhaseName.SECOND_PLACEMENT)(
        actions.handle_second_placement
    )
    registry.register(entities.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.register(entities.GamePhaseName.DISCARD_RESOURCES)(
        actions.handle_discard_resources
    )
    registry.register(entities.GamePhaseName.DICE_PLAY_WARRIOR)(
        actions.handle_dice_play_warrior
    )
    registry.register(entities.GamePhaseName.DICE_PLAY_MAMO)(
        actions.handle_dice_play_mamo
    )
    registry.register(entities.GamePhaseName.DICE_PLAY_BLESSED)(
        actions.handle_dice_play_blessed
    )
    registry.register(entities.GamePhaseName.DICE_PLAY_PATHFINDER)(
        actions.handle_dice_play_pathfinder
    )
    registry.register(entities.GamePhaseName.MOVE_CONQUISTATOR)(
        actions.handle_move_conquistator
    )
    registry.register(entities.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    registry.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR)(
        actions.handle_move_conquistator
    )
    registry.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO)(
        actions.handle_trade_and_build_play_mamo
    )
    registry.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED)(
        actions.handle_trade_and_build_play_blessed
    )
    registry.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER)(
        actions.handle_trade_and_build_play_pathfinder
    )

    for phase, on_timeout in (
        (entities.GamePhaseName.FIRST_PLACEMENT, timeouts.timeout_first_placement),
        (entities.GamePhaseName.SECOND_PLACEMENT, timeouts.timeout_second_placement),
        (entities.GamePhaseName.DICE_ROLL, timeouts.timeout_dice_roll),
        (entities.GamePhaseName.DISCARD_RESOURCES, timeouts.timeout_discard_resources),
        (entities.GamePhaseName.MOVE_CONQUISTATOR, timeouts.timeout_move_conquistator),
        (entities.GamePhaseName.DICE_PLAY_WARRIOR, timeouts.timeout_move_conquistator),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
            timeouts.timeout_move_conquistator,
        ),
        (entities.GamePhaseName.DICE_PLAY_MAMO, timeouts.timeout_play_mamo),
        (entities.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO, timeouts.timeout_play_mamo),
        (entities.GamePhaseName.DICE_PLAY_BLESSED, timeouts.timeout_play_blessed),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
            timeouts.timeout_play_blessed,
        ),
        (entities.GamePhaseName.DICE_PLAY_PATHFINDER, timeouts.timeout_play_pathfinder),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
            timeouts.timeout_play_pathfinder,
        ),
        (entities.GamePhaseName.TRADE_AND_BUILD, timeouts.timeout_trade_and_build),
    ):
        registry.set_timeout(phase, ZERO, on_timeout)

    return registry


def _create_stored_game(
    *,
    phase: entities.GamePhaseName,
    setup: Callable[[entities.Game], None] | None = None,
) -> tuple[
    uuid.UUID,
    repository_module.InMemoryGameRepository,
    actions.ActionsRegistry,
]:
    repository = repository_module.InMemoryGameRepository()
    board = services.generate_map()
    desert = next(hex_ for hex_ in board if hex_.type is entities.HexType.DESERT)
    game = entities.Game(
        map=board,
        conquistator_location=entities.HexLocation(q=desert.q, r=desert.r),
        players={
            nickname: entities.Player()
            for nickname in ("player-0", "player-1", "player-2")
        },
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    if setup is not None:
        setup(game)
    game.phase = phase
    game.phase_deadline = NOW
    game_id = repository.add(game)
    return game_id, repository, _zero_timeout_registry()


async def _apply_due(
    game_id: uuid.UUID,
    repository: repository_module.InMemoryGameRepository,
    registry: actions.ActionsRegistry,
    *,
    rng: random.Random | None = None,
    event_broker: broker.EventBroker | None = None,
) -> actions.ActionExecutionResult | None:
    return await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=locks.GameLockManager(),
        broker=event_broker or broker.EventBroker(),
        rng=rng or random.Random(0),
        now=NOW,
    )
