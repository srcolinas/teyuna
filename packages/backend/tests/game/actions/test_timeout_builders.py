import collections
import datetime
import random

import pytest

from src.game import actions, entities
from src.game.actions import timeouts


@pytest.fixture
def game() -> entities.Game:
    nicknames = ("player-0", "player-1", "player-2")
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=1)
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=entities.HexLocation(q=mountains.q, r=mountains.r),
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
    action = timeouts.timeout_dice_roll(game, random.Random(0))

    assert type(action) is actions.PlayerAction
    assert action.by == game.active_player


def test_timeout_trade_and_build_returns_active_player_action(
    game: entities.Game,
) -> None:
    action = timeouts.timeout_trade_and_build(game, random.Random(0))

    assert type(action) is actions.PlayerAction
    assert action.by == game.active_player


def test_timeout_first_placement_returns_explicit_free_placement(
    game: entities.Game,
) -> None:
    action = timeouts.timeout_first_placement(game, random.Random(0))

    assert action == actions.FreePlacementAction(
        by=game.active_player,
        due_to_timeout=True,
        terrace=entities.Coordinate(q=-2, r=0, d=4),
        path=entities.Coordinate(q=-2, r=0, d=4),
        rng_=action.rng_,
    )


def test_timeout_second_placement_returns_explicit_free_placement(
    game: entities.Game,
) -> None:
    action = timeouts.timeout_second_placement(game, random.Random(1))

    assert action == actions.FreePlacementAction(
        by=game.active_player,
        due_to_timeout=True,
        terrace=entities.Coordinate(q=0, r=-2, d=1),
        path=entities.Coordinate(q=0, r=-2, d=1),
        rng_=action.rng_,
    )


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
        {entities.ResourceCard.WOOD: 2}
    )

    action = timeouts.timeout_move_conquistator(game, random.Random(0))

    assert action == actions.MoveConquistatorAction(
        by=active,
        due_to_timeout=True,
        q=0,
        r=1,
        from_player=victim,
        rng_=action.rng_,
    )


def test_timeout_move_conquistator_without_victims_sets_from_player_none() -> None:
    game = _multi_hex_game()

    action = timeouts.timeout_move_conquistator(game, random.Random(0))

    assert action == actions.MoveConquistatorAction(
        by=game.active_player,
        due_to_timeout=True,
        q=0,
        r=1,
        from_player=None,
        rng_=action.rng_,
    )


def test_timeout_discard_resources_returns_explicit_count(
    game: entities.Game,
) -> None:
    game.players["player-0"].resources = collections.Counter(
        {
            entities.ResourceCard.WOOD: 5,
            entities.ResourceCard.GOLD: 4,
        }
    )
    game.to_discard_resources = {"player-0": 4}

    action = timeouts.timeout_discard_resources(game, random.Random(0))

    assert action == actions.DiscardResourcesAction(
        by="player-0",
        due_to_timeout=True,
        count=collections.Counter(
            {
                entities.ResourceCard.GOLD: 2,
                entities.ResourceCard.WOOD: 2,
            }
        ),
        rng_=action.rng_,
    )


def test_timeout_play_mamo_returns_explicit_resource(
    game: entities.Game,
) -> None:
    action = timeouts.timeout_play_mamo(game, random.Random(0))

    assert action == actions.PlayMamoAction(
        by=game.active_player,
        due_to_timeout=True,
        resource=entities.ResourceCard.MAIZE,
        rng_=action.rng_,
    )


def test_timeout_play_blessed_samples_from_supply(
    game: entities.Game,
) -> None:
    action = timeouts.timeout_play_blessed(game, random.Random(0))

    assert action == actions.PlayBlessedAction(
        by=game.active_player,
        due_to_timeout=True,
        resources=(entities.ResourceCard.COTTON, entities.ResourceCard.COTTON),
        rng_=action.rng_,
    )


def test_timeout_play_blessed_falls_back_when_supply_too_small(
    game: entities.Game,
) -> None:
    game.resource_supply = collections.Counter()

    action = timeouts.timeout_play_blessed(game, random.Random(0))

    assert action == actions.PlayBlessedAction(
        by=game.active_player,
        due_to_timeout=True,
        resources=(entities.ResourceCard.GOLD, entities.ResourceCard.STONE),
        rng_=action.rng_,
    )


def test_timeout_play_pathfinder_returns_empty_when_no_legal_paths(
    game: entities.Game,
) -> None:
    action = timeouts.timeout_play_pathfinder(game, random.Random(0))

    assert action == actions.PlayPathfinderAction(
        by=game.active_player,
        due_to_timeout=True,
        paths=(),
        rng_=action.rng_,
    )


def test_timeout_play_pathfinder_returns_explicit_paths(
    game: entities.Game,
) -> None:
    game.use_vertex(
        game.active_player,
        entities.canonical_vertex(0, 0, 0),
        entities.SettlementType.TERRACE,
    )

    action = timeouts.timeout_play_pathfinder(game, random.Random(0))

    assert action == actions.PlayPathfinderAction(
        by=game.active_player,
        due_to_timeout=True,
        paths=(
            entities.Coordinate(q=0, r=-1, d=1),
            entities.Coordinate(q=0, r=-1, d=2),
        ),
        rng_=action.rng_,
    )


def _multi_hex_game() -> entities.Game:
    nicknames = ("player-0", "player-1", "player-2")
    game_ = entities.Game(
        map=(
            entities.Hex(q=0, r=0, type=entities.HexType.DESERT, number=7),
            entities.Hex(q=1, r=0, type=entities.HexType.MOUNTAINS, number=6),
            entities.Hex(q=0, r=1, type=entities.HexType.JUNGLE, number=5),
        ),
        conquistator_location=entities.HexLocation(q=0, r=0),
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
