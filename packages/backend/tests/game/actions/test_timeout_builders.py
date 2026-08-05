import collections
import datetime
import random

import pytest

from src.game import entities
from src.game import actions
from src.game.actions import timeouts
import teyuna_core


@pytest.fixture
def game() -> entities.Game:
    nicknames = ("player-0", "player-1", "player-2")
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=1
    )
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_core.HexLocation(q=mountains.q, r=mountains.r),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in nicknames
        },
        available_slots=0,
    )
    game_.start(datetime.timedelta(seconds=60))
    return game_


def test_timeout_dice_roll_returns_active_player_action(
    game: entities.Game,
) -> None:
    timeout_action = timeouts.timeout_dice_roll(game, random.Random(0))
    action = timeout_action.action

    assert type(action) is teyuna_core.PlayerAction
    assert timeout_action.by == game.active_player


def test_timeout_trade_and_build_returns_active_player_action(
    game: entities.Game,
) -> None:
    timeout_action = timeouts.timeout_trade_and_build(game, random.Random(0))
    action = timeout_action.action

    assert type(action) is teyuna_core.PlayerAction
    assert timeout_action.by == game.active_player


def test_timeout_first_placement_returns_explicit_free_placement(
    game: entities.Game,
) -> None:
    timeout_action = timeouts.timeout_first_placement(game, random.Random(0))
    action = timeout_action.action

    assert type(action) is teyuna_core.FreePlacementAction
    assert timeout_action.by == game.active_player
    assert action.terrace is not None
    assert action.path is not None
    assert action.terrace in teyuna_core.vertices_of_edge(action.path)


def test_timeout_second_placement_returns_explicit_free_placement(
    game: entities.Game,
) -> None:
    timeout_action = timeouts.timeout_second_placement(game, random.Random(1))
    action = timeout_action.action

    assert type(action) is teyuna_core.FreePlacementAction
    assert timeout_action.by == game.active_player
    assert action.terrace is not None
    assert action.path is not None
    assert action.terrace in teyuna_core.vertices_of_edge(action.path)


def test_resolve_free_placement_fills_missing_path(
    game: entities.Game,
) -> None:
    terrace = teyuna_core.Coordinate(q=0, r=-1, d=2)
    action = timeouts.resolve_free_placement(
        game,
        actions.ExecutionContext(
            by=game.active_player,
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        teyuna_core.FreePlacementAction(terrace=terrace),
    )

    assert action.terrace == terrace
    assert action.path is not None


def test_resolve_free_placement_fills_missing_terrace(
    game: entities.Game,
) -> None:
    path = teyuna_core.Coordinate(q=0, r=-1, d=2)
    action = timeouts.resolve_free_placement(
        game,
        actions.ExecutionContext(
            by=game.active_player,
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        teyuna_core.FreePlacementAction(path=path),
    )

    assert action.path == path
    assert action.terrace is not None
    assert action.terrace in teyuna_core.vertices_of_edge(path)


def test_resolve_free_placement_keeps_both_when_provided(
    game: entities.Game,
) -> None:
    terrace = teyuna_core.Coordinate(q=0, r=-1, d=2)
    path = teyuna_core.Coordinate(q=0, r=-1, d=2)
    action = timeouts.resolve_free_placement(
        game,
        actions.ExecutionContext(
            by=game.active_player,
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        teyuna_core.FreePlacementAction(terrace=terrace, path=path),
    )

    assert action.terrace == terrace
    assert action.path == path


def test_pick_free_placement_raises_when_no_legal_move_available(
    game: entities.Game,
) -> None:
    dummy = game.active_player
    for edge in list(game.free_edges):
        game.use_edge(dummy, edge)

    with pytest.raises(RuntimeError):
        timeouts.timeout_first_placement(game, random.Random(0))


def test_timeout_move_conquistator_returns_explicit_move() -> None:
    game = _multi_hex_game()
    active = game.active_player
    victim = next(n for n in game.turn_order if n != active)
    game.players[victim].resources = collections.Counter(
        {teyuna_core.ResourceCard.WOOD: 2}
    )

    timeout_action = timeouts.timeout_move_conquistator(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == active

    assert action == teyuna_core.MoveConquistatorAction(
        q=0,
        r=1,
        from_player=victim,
    )


def test_timeout_move_conquistator_without_victims_sets_from_player_none() -> None:
    game = _multi_hex_game()

    timeout_action = timeouts.timeout_move_conquistator(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == game.active_player

    assert action == teyuna_core.MoveConquistatorAction(
        q=0,
        r=1,
        from_player=None,
    )


def test_timeout_discard_resources_returns_explicit_count(
    game: entities.Game,
) -> None:
    game.players["player-0"].resources = collections.Counter(
        {
            teyuna_core.ResourceCard.WOOD: 5,
            teyuna_core.ResourceCard.GOLD: 4,
        }
    )
    game.to_discard_resources = {"player-0": 4}

    timeout_action = timeouts.timeout_discard_resources(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == "player-0"

    assert action == teyuna_core.DiscardResourcesAction(
        count=collections.Counter(
            {
                teyuna_core.ResourceCard.GOLD: 2,
                teyuna_core.ResourceCard.WOOD: 2,
            }
        ),
    )


def test_timeout_play_mamo_returns_explicit_resource(
    game: entities.Game,
) -> None:
    timeout_action = timeouts.timeout_play_mamo(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == game.active_player

    assert action == teyuna_core.PlayMamoAction(
        resource=teyuna_core.ResourceCard.MAIZE,
    )


def test_timeout_play_blessed_samples_from_supply(
    game: entities.Game,
) -> None:
    timeout_action = timeouts.timeout_play_blessed(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == game.active_player

    assert action == teyuna_core.PlayBlessedAction(
        resources=(
            teyuna_core.ResourceCard.COTTON,
            teyuna_core.ResourceCard.COTTON,
        ),
    )


def test_timeout_play_blessed_falls_back_when_supply_too_small(
    game: entities.Game,
) -> None:
    game.resource_supply = collections.Counter()

    timeout_action = timeouts.timeout_play_blessed(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == game.active_player

    assert action == teyuna_core.PlayBlessedAction(
        resources=(teyuna_core.ResourceCard.GOLD, teyuna_core.ResourceCard.STONE),
    )


def test_timeout_play_pathfinder_returns_empty_when_no_legal_paths(
    game: entities.Game,
) -> None:
    timeout_action = timeouts.timeout_play_pathfinder(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == game.active_player

    assert action == teyuna_core.PlayPathfinderAction(
        paths=(),
    )


def test_timeout_play_pathfinder_returns_explicit_paths(
    game: entities.Game,
) -> None:
    game.use_vertex(
        game.active_player,
        teyuna_core.canonical_vertex(0, 0, 0),
        teyuna_core.SettlementType.TERRACE,
    )

    timeout_action = timeouts.timeout_play_pathfinder(game, random.Random(0))
    action = timeout_action.action
    assert timeout_action.by == game.active_player

    assert action == teyuna_core.PlayPathfinderAction(
        paths=(
            teyuna_core.Coordinate(q=0, r=-1, d=1),
            teyuna_core.Coordinate(q=0, r=-1, d=2),
        ),
    )


def _multi_hex_game() -> entities.Game:
    nicknames = ("player-0", "player-1", "player-2")
    game_ = entities.Game(
        map=(
            teyuna_core.MapHex(q=0, r=0, type=teyuna_core.HexType.DESERT, number=7),
            teyuna_core.MapHex(q=1, r=0, type=teyuna_core.HexType.MOUNTAINS, number=6),
            teyuna_core.MapHex(q=0, r=1, type=teyuna_core.HexType.JUNGLE, number=5),
        ),
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in nicknames
        },
        available_slots=0,
    )
    game_.start(datetime.timedelta(seconds=60))
    return game_
