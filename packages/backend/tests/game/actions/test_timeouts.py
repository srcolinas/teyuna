import asyncio
import collections
import datetime
import random
import uuid
from typing import cast

import pytest

import teyuna_core

from src.game import (
    actions,
    broker,
    entities,
    locks,
    repository as repository_module,
    services,
)
from src.game.actions import timeouts


def test_set_timeout_and_timeout_for() -> None:
    registry = actions.ActionsRegistry()
    try:
        registry.timeout_for(teyuna_core.GamePhaseName.DICE_ROLL)
        raise AssertionError("expected KeyError")
    except KeyError as e:
        assert "dice roll" in str(e)

    registry.set_timeout(
        teyuna_core.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    timeout = registry.timeout_for(teyuna_core.GamePhaseName.DICE_ROLL)
    assert timeout.duration == datetime.timedelta(seconds=30)
    assert timeout.on_timeout is timeouts.timeout_dice_roll


def test_timeout_dice_roll_executes(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    rng = random.Random(0)
    action = timeouts.timeout_dice_roll(game, rng)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    result = cast(
        teyuna_core.DiceRollResult,
        registry.execute(game, action),
    )
    assert result.error is None
    assert 1 <= result.die_1 <= 6
    assert 1 <= result.die_2 <= 6
    assert result.to_discard == dict(game.to_discard_resources)
    assert result.next_phase in {
        teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        teyuna_core.GamePhaseName.DISCARD_RESOURCES,
        teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
    }


def test_timeout_trade_and_build_ends_turn(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    active = game.active_player
    action = timeouts.timeout_trade_and_build(game, random.Random(0))
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    result = cast(
        teyuna_core.EndedTradeAndBuildResult,
        registry.execute(game, action),
    )
    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.next_player == game.active_player
    assert game.active_player != active


def test_timeout_first_placement_executes() -> None:
    repository = repository_module.InMemoryGameRepository()
    game_id = _create_started_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    game = repository.retrieve(game_id)
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(
        actions.handle_first_placement
    )
    action = timeouts.timeout_first_placement(game, random.Random(1))
    result = cast(
        teyuna_core.PlacedBuildingsResult,
        registry.execute(game, action),
    )
    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.FIRST_PLACEMENT
    assert result.settlement == action.terrace
    assert result.path == action.path
    assert len(list(game.players[action.by].settlements.locations())) == 1
    assert len(game.players[action.by].paths) == 1


def test_timeout_discard_resources_executes(game: entities.Game) -> None:
    nick = game.active_player
    game.players[nick].resources = collections.Counter(
        {
            teyuna_core.ResourceCard.WOOD: 5,
            teyuna_core.ResourceCard.GOLD: 4,
        }
    )
    game.to_discard_resources = {nick: 4}
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DISCARD_RESOURCES)(
        actions.handle_discard_resources
    )
    action = timeouts.timeout_discard_resources(game, random.Random(0))
    game.phase = teyuna_core.GamePhaseName.DISCARD_RESOURCES
    result = cast(
        teyuna_core.DiscardedResourcesResult,
        registry.execute(game, action),
    )
    assert nick not in game.to_discard_resources
    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.MOVE_CONQUISTATOR
    assert result.count == action.count


def test_timeout_move_conquistator_executes() -> None:
    repository = repository_module.InMemoryGameRepository()
    game_id = _create_started_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    game = repository.retrieve(game_id)
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.MOVE_CONQUISTATOR)(
        actions.handle_move_conquistator
    )
    before = game.conquistator_location
    action = timeouts.timeout_move_conquistator(game, random.Random(2))
    game.phase = teyuna_core.GamePhaseName.MOVE_CONQUISTATOR
    result = cast(
        teyuna_core.MovedConquistatorResult,
        registry.execute(game, action),
    )
    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.q == action.q
    assert result.r == action.r
    assert result.from_player is action.from_player
    assert result.stolen is None
    assert game.conquistator_location != before


def test_timeout_play_mamo_and_blessed(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DICE_PLAY_MAMO)(
        actions.handle_dice_play_mamo
    )
    registry.register(teyuna_core.GamePhaseName.DICE_PLAY_BLESSED)(
        actions.handle_dice_play_blessed
    )
    game.phase = teyuna_core.GamePhaseName.DICE_PLAY_MAMO
    mamo = timeouts.timeout_play_mamo(game, random.Random(0))
    mamo_result = cast(
        teyuna_core.PlayedMamoResult,
        registry.execute(game, mamo),
    )
    assert mamo_result.error is None
    assert mamo_result.resource is mamo.resource
    assert mamo_result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    game.phase = teyuna_core.GamePhaseName.DICE_PLAY_BLESSED
    blessed = timeouts.timeout_play_blessed(game, random.Random(0))
    blessed_result = cast(
        teyuna_core.PlayedBlessedResult,
        registry.execute(game, blessed),
    )
    assert blessed_result.error is None
    assert blessed_result.resources == blessed.resources
    assert blessed_result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL


def test_timeout_play_pathfinder_allows_empty(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER)(
        actions.handle_dice_play_pathfinder
    )
    action = timeouts.timeout_play_pathfinder(game, random.Random(0))
    assert action.paths == ()
    game.phase = teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER
    result = cast(
        teyuna_core.PlayedPathfinderResult,
        registry.execute(game, action),
    )
    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.paths == ()


@pytest.mark.asyncio
async def test_apply_player_action_resets_deadline() -> None:
    repository = repository_module.InMemoryGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.set_timeout(
        teyuna_core.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        datetime.timedelta(seconds=90),
        timeouts.timeout_trade_and_build,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
        datetime.timedelta(seconds=30),
        timeouts.timeout_move_conquistator,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.DISCARD_RESOURCES,
        datetime.timedelta(seconds=45),
        timeouts.timeout_discard_resources,
    )
    game_locks = locks.GameLockManager()
    event_broker = broker.EventBroker()
    game_id = _create_started_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    game = repository.retrieve(game_id)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = now + datetime.timedelta(seconds=5)
    repository.update(game_id, game)
    game = repository.retrieve(game_id)
    active_player = game.active_player

    waiter = asyncio.create_task(_next_broker_event(event_broker, game_id))
    await asyncio.sleep(0)

    action = teyuna_core.PlayerAction(by=active_player, rng_=random.Random(0))
    result, _ = await services.apply_player_action(
        game_id,
        action,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=event_broker,
        now=now,
    )
    assert result.action == action

    assert result.action.by == active_player
    published = await waiter
    assert published.data is result

    stored = repository.retrieve(game_id)
    assert stored.phase is result.next_phase
    timeout = registry.timeout_for(result.next_phase)
    assert timeout is not None
    assert stored.phase_deadline == now + timeout.duration


@pytest.mark.asyncio
async def test_apply_timeout_if_due_is_noop_when_not_expired() -> None:
    repository = repository_module.InMemoryGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.set_timeout(
        teyuna_core.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    game_locks = locks.GameLockManager()
    event_broker = broker.EventBroker()
    game_id = _create_started_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    game = repository.retrieve(game_id)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = now + datetime.timedelta(seconds=10)
    repository.update(game_id, game)
    result = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=event_broker,
        rng=random.Random(0),
        now=now,
    )
    assert result is None
    assert event_broker._next_id[game_id] == 0
    assert repository.retrieve(game_id).phase is teyuna_core.GamePhaseName.DICE_ROLL


@pytest.mark.asyncio
async def test_apply_timeout_if_due_advances_phase() -> None:
    repository = repository_module.InMemoryGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.set_timeout(
        teyuna_core.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        datetime.timedelta(seconds=90),
        timeouts.timeout_trade_and_build,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
        datetime.timedelta(seconds=30),
        timeouts.timeout_move_conquistator,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.DISCARD_RESOURCES,
        datetime.timedelta(seconds=45),
        timeouts.timeout_discard_resources,
    )
    game_locks = locks.GameLockManager()
    event_broker = broker.EventBroker()
    game_id = _create_started_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    game = repository.retrieve(game_id)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = now - datetime.timedelta(seconds=1)
    repository.update(game_id, game)

    waiter = asyncio.create_task(_next_broker_event(event_broker, game_id))
    await asyncio.sleep(0)

    result = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=event_broker,
        rng=random.Random(0),
        now=now,
    )

    assert result is not None
    assert result.error is None
    assert result.action.due_to_timeout is True
    published = await waiter
    assert published.data is result
    assert repository.retrieve(game_id).phase is not teyuna_core.GamePhaseName.DICE_ROLL


@pytest.mark.asyncio
async def test_second_timeout_is_noop_after_deadline_refresh() -> None:
    repository = repository_module.InMemoryGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        datetime.timedelta(seconds=90),
        timeouts.timeout_trade_and_build,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
        datetime.timedelta(seconds=30),
        timeouts.timeout_move_conquistator,
    )
    registry.set_timeout(
        teyuna_core.GamePhaseName.DISCARD_RESOURCES,
        datetime.timedelta(seconds=45),
        timeouts.timeout_discard_resources,
    )
    game_locks = locks.GameLockManager()
    event_broker = broker.EventBroker()
    game_id = _create_started_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    game = repository.retrieve(game_id)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = now - datetime.timedelta(seconds=1)
    repository.update(game_id, game)
    first = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=event_broker,
        rng=random.Random(0),
        now=now,
    )
    assert first is not None
    assert first.action.due_to_timeout is True
    assert event_broker._next_id[game_id] == 1

    phase_after = repository.retrieve(game_id).phase
    second = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=event_broker,
        rng=random.Random(0),
        now=now,
    )
    assert second is None
    assert event_broker._next_id[game_id] == 1
    assert repository.retrieve(game_id).phase is phase_after


@pytest.mark.asyncio
async def test_apply_timeout_if_due_is_noop_when_deadline_is_none() -> None:
    repository = repository_module.InMemoryGameRepository()
    registry = actions.ActionsRegistry()
    game_locks = locks.GameLockManager()
    event_broker = broker.EventBroker()
    game_id = _create_started_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    game = repository.retrieve(game_id)
    game.phase = teyuna_core.GamePhaseName.END_GAME
    game.phase_deadline = None
    repository.update(game_id, game)
    result = await services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=event_broker,
        rng=random.Random(0),
        now=now,
    )
    assert result is None
    assert event_broker._next_id[game_id] == 0
    assert repository.retrieve(game_id).phase is teyuna_core.GamePhaseName.END_GAME


async def _next_broker_event(
    event_broker: broker.EventBroker, game_id: uuid.UUID
) -> broker.Event:
    async for event in event_broker.iterate(game_id):
        return event
    raise AssertionError("expected a broker event")


def _create_started_game(
    repository: repository_module.InMemoryGameRepository,
    players: list[str],
    first_placement_timeout: datetime.timedelta,
) -> uuid.UUID:
    board = services.generate_map()
    desert = next(hex_ for hex_ in board if hex_.type is teyuna_core.HexType.DESERT)
    game = entities.Game(
        map=board,
        conquistator_location=teyuna_core.HexLocation(q=desert.q, r=desert.r),
        players={nickname: entities.Player() for nickname in players},
        available_slots=0,
    )
    game.start(first_placement_timeout)
    return repository.add(game)
