import collections
import datetime
import random
from typing import cast

from src.active import (
    actions,
    entities,
    locks,
    repository as repository_module,
    services,
)
from src.active.actions import timeouts


def test_set_timeout_and_timeout_for() -> None:
    registry = actions.ActionsRegistry()
    try:
        registry.timeout_for(actions.GamePhaseName.DICE_ROLL)
        raise AssertionError("expected KeyError")
    except KeyError as e:
        assert "dice roll" in str(e)

    registry.set_timeout(
        actions.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    timeout = registry.timeout_for(actions.GamePhaseName.DICE_ROLL)
    assert timeout.duration == datetime.timedelta(seconds=30)
    assert timeout.on_timeout is timeouts.timeout_dice_roll


def test_timeout_dice_roll_executes(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    rng = random.Random(0)
    action = timeouts.timeout_dice_roll(game, rng)
    result = cast(
        actions.DiceRollResult,
        registry.execute(actions.GamePhaseName.DICE_ROLL, game, action),
    )
    assert result.succeeded is True
    assert result.error is None
    assert 1 <= result.die_1 <= 6
    assert 1 <= result.die_2 <= 6
    assert result.to_discard == dict(game.to_discard_resources)
    assert result.phase in {
        actions.GamePhaseName.TRADE_AND_BUILD,
        actions.GamePhaseName.DISCARD_RESOURCES,
        actions.GamePhaseName.MOVE_CONQUISTATOR,
    }


def test_timeout_trade_and_build_ends_turn(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    active = game.active_player
    action = timeouts.timeout_trade_and_build(game, random.Random(0))
    result = cast(
        actions.EndedTradeAndBuildResult,
        registry.execute(actions.GamePhaseName.TRADE_AND_BUILD, game, action),
    )
    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.next_player == game.active_player
    assert game.active_player != active


def test_timeout_first_placement_executes() -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    game = repository.retrieve(game_id).game
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(
        actions.handle_first_placement
    )
    action = timeouts.timeout_first_placement(game, random.Random(1))
    result = cast(
        actions.PlacedBuildingsResult,
        registry.execute(actions.GamePhaseName.FIRST_PLACEMENT, game, action),
    )
    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.FIRST_PLACEMENT
    assert result.settlement == action.terrace
    assert result.path == action.path
    assert len(list(game.players[action.by].settlements.locations())) == 1
    assert len(game.players[action.by].paths) == 1


def test_timeout_discard_resources_executes(game: entities.ActiveGame) -> None:
    nick = game.active_player
    game.players[nick].resources = collections.Counter(
        {
            entities.ResourceCard.WOOD: 5,
            entities.ResourceCard.GOLD: 4,
        }
    )
    game.to_discard_resources = {nick: 4}
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DISCARD_RESOURCES)(
        actions.handle_discard_resources
    )
    action = timeouts.timeout_discard_resources(game, random.Random(0))
    result = cast(
        actions.DiscardedResourcesResult,
        registry.execute(actions.GamePhaseName.DISCARD_RESOURCES, game, action),
    )
    assert nick not in game.to_discard_resources
    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.MOVE_CONQUISTATOR
    assert result.count == action.count


def test_timeout_move_conquistator_executes() -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    game = repository.retrieve(game_id).game
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.MOVE_CONQUISTATOR)(
        actions.handle_move_conquistator
    )
    before = game.conquistator_location
    action = timeouts.timeout_move_conquistator(game, random.Random(2))
    result = cast(
        actions.MovedConquistatorResult,
        registry.execute(actions.GamePhaseName.MOVE_CONQUISTATOR, game, action),
    )
    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.q == action.q
    assert result.r == action.r
    assert result.from_player is action.from_player
    assert result.stolen is None
    assert game.conquistator_location != before


def test_timeout_play_mamo_and_blessed(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DICE_PLAY_MAMO)(
        actions.handle_dice_play_mamo
    )
    registry.register(actions.GamePhaseName.DICE_PLAY_BLESSED)(
        actions.handle_dice_play_blessed
    )
    mamo = timeouts.timeout_play_mamo(game, random.Random(0))
    mamo_result = cast(
        actions.PlayedMamoResult,
        registry.execute(actions.GamePhaseName.DICE_PLAY_MAMO, game, mamo),
    )
    assert mamo_result.succeeded is True
    assert mamo_result.resource is mamo.resource
    assert mamo_result.phase is actions.GamePhaseName.DICE_ROLL
    blessed = timeouts.timeout_play_blessed(game, random.Random(0))
    blessed_result = cast(
        actions.PlayedBlessedResult,
        registry.execute(actions.GamePhaseName.DICE_PLAY_BLESSED, game, blessed),
    )
    assert blessed_result.succeeded is True
    assert blessed_result.resources == blessed.resources
    assert blessed_result.phase is actions.GamePhaseName.DICE_ROLL


def test_timeout_play_pathfinder_allows_empty(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DICE_PLAY_PATHFINDER)(
        actions.handle_dice_play_pathfinder
    )
    action = timeouts.timeout_play_pathfinder(game, random.Random(0))
    assert action.paths == ()
    result = cast(
        actions.PlayedPathfinderResult,
        registry.execute(actions.GamePhaseName.DICE_PLAY_PATHFINDER, game, action),
    )
    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.paths == ()


def test_apply_player_action_resets_deadline() -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.set_timeout(
        actions.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    registry.set_timeout(
        actions.GamePhaseName.TRADE_AND_BUILD,
        datetime.timedelta(seconds=90),
        timeouts.timeout_trade_and_build,
    )
    registry.set_timeout(
        actions.GamePhaseName.MOVE_CONQUISTATOR,
        datetime.timedelta(seconds=30),
        timeouts.timeout_move_conquistator,
    )
    registry.set_timeout(
        actions.GamePhaseName.DISCARD_RESOURCES,
        datetime.timedelta(seconds=45),
        timeouts.timeout_discard_resources,
    )
    game_locks = locks.GameLockManager()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    repository.update(
        game_id,
        repository.retrieve(game_id).game,
        actions.GamePhaseName.DICE_ROLL,
        phase_deadline=now + datetime.timedelta(seconds=5),
    )
    game = repository.retrieve(game_id).game
    result, _ = services.apply_player_action(
        game_id,
        actions.PlayerAction(by=game.active_player, rng_=random.Random(0)),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        now=now,
    )
    stored = repository.retrieve(game_id)
    assert stored.phase is result.phase
    timeout = registry.timeout_for(result.phase)
    assert timeout is not None
    assert stored.phase_deadline == now + timeout.duration


def test_apply_timeout_if_due_is_noop_when_not_expired() -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.set_timeout(
        actions.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    game_locks = locks.GameLockManager()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    repository.update(
        game_id,
        repository.retrieve(game_id).game,
        actions.GamePhaseName.DICE_ROLL,
        phase_deadline=now + datetime.timedelta(seconds=10),
    )
    services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        rng=random.Random(0),
        now=now,
    )
    assert repository.retrieve(game_id).phase is actions.GamePhaseName.DICE_ROLL


def test_apply_timeout_if_due_advances_phase() -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.set_timeout(
        actions.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    registry.set_timeout(
        actions.GamePhaseName.TRADE_AND_BUILD,
        datetime.timedelta(seconds=90),
        timeouts.timeout_trade_and_build,
    )
    registry.set_timeout(
        actions.GamePhaseName.MOVE_CONQUISTATOR,
        datetime.timedelta(seconds=30),
        timeouts.timeout_move_conquistator,
    )
    registry.set_timeout(
        actions.GamePhaseName.DISCARD_RESOURCES,
        datetime.timedelta(seconds=45),
        timeouts.timeout_discard_resources,
    )
    game_locks = locks.GameLockManager()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    repository.update(
        game_id,
        repository.retrieve(game_id).game,
        actions.GamePhaseName.DICE_ROLL,
        phase_deadline=now - datetime.timedelta(seconds=1),
    )
    services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        rng=random.Random(0),
        now=now,
    )
    assert repository.retrieve(game_id).phase is not actions.GamePhaseName.DICE_ROLL


def test_second_timeout_is_noop_after_deadline_refresh() -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    registry.register(actions.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    registry.set_timeout(
        actions.GamePhaseName.DICE_ROLL,
        datetime.timedelta(seconds=30),
        timeouts.timeout_dice_roll,
    )
    registry.set_timeout(
        actions.GamePhaseName.TRADE_AND_BUILD,
        datetime.timedelta(seconds=90),
        timeouts.timeout_trade_and_build,
    )
    registry.set_timeout(
        actions.GamePhaseName.MOVE_CONQUISTATOR,
        datetime.timedelta(seconds=30),
        timeouts.timeout_move_conquistator,
    )
    registry.set_timeout(
        actions.GamePhaseName.DISCARD_RESOURCES,
        datetime.timedelta(seconds=45),
        timeouts.timeout_discard_resources,
    )
    game_locks = locks.GameLockManager()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    repository.update(
        game_id,
        repository.retrieve(game_id).game,
        actions.GamePhaseName.DICE_ROLL,
        phase_deadline=now - datetime.timedelta(seconds=1),
    )
    services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        rng=random.Random(0),
        now=now,
    )
    phase_after = repository.retrieve(game_id).phase
    services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        rng=random.Random(0),
        now=now,
    )
    assert repository.retrieve(game_id).phase is phase_after


def test_apply_timeout_if_due_is_noop_when_deadline_is_none() -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    registry = actions.ActionsRegistry()
    game_locks = locks.GameLockManager()
    game_id = services.create_game(
        repository,
        players=["player-0", "player-1", "player-2"],
        first_placement_timeout=datetime.timedelta(seconds=60),
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    game = repository.retrieve(game_id).game
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.END_GAME,
        phase_deadline=None,
    )
    services.apply_timeout_if_due(
        game_id,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        rng=random.Random(0),
        now=now,
    )
    assert repository.retrieve(game_id).phase is actions.GamePhaseName.END_GAME
