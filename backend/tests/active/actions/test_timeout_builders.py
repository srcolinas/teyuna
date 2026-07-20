import collections
import random

from src.active import actions, entities
from src.active.actions import timeouts


def test_timeout_dice_roll_returns_active_player_action(
    game: entities.ActiveGame,
) -> None:
    action = timeouts.timeout_dice_roll(game, random.Random(0))

    assert type(action) is actions.PlayerAction
    assert action.by == "player-0"


def test_timeout_trade_and_build_returns_active_player_action(
    game: entities.ActiveGame,
) -> None:
    action = timeouts.timeout_trade_and_build(game, random.Random(0))

    assert type(action) is actions.PlayerAction
    assert action.by == "player-0"


def test_timeout_first_placement_returns_explicit_free_placement(
    game: entities.ActiveGame,
) -> None:
    action = timeouts.timeout_first_placement(game, random.Random(0))

    assert action == actions.FreePlacementAction(
        by="player-0",
        terrace=entities.Coordinate(q=-2, r=0, d=4),
        path=entities.Coordinate(q=-2, r=0, d=4),
        rng_=action.rng_,
    )


def test_timeout_second_placement_returns_explicit_free_placement(
    game: entities.ActiveGame,
) -> None:
    action = timeouts.timeout_second_placement(game, random.Random(1))

    assert action == actions.FreePlacementAction(
        by="player-0",
        terrace=entities.Coordinate(q=0, r=-2, d=1),
        path=entities.Coordinate(q=0, r=-2, d=1),
        rng_=action.rng_,
    )


def test_timeout_move_conquistator_returns_explicit_move() -> None:
    game = _multi_hex_game()
    game.players["player-1"].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 2}
    )

    action = timeouts.timeout_move_conquistator(game, random.Random(0))

    assert action == actions.MoveConquistatorAction(
        by="player-0",
        q=0,
        r=1,
        from_player="player-1",
        rng_=action.rng_,
    )


def test_timeout_move_conquistator_without_victims_sets_from_player_none() -> None:
    game = _multi_hex_game()

    action = timeouts.timeout_move_conquistator(game, random.Random(0))

    assert action == actions.MoveConquistatorAction(
        by="player-0",
        q=0,
        r=1,
        from_player=None,
        rng_=action.rng_,
    )


def test_timeout_discard_resources_returns_explicit_count(
    game: entities.ActiveGame,
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
        count=collections.Counter(
            {
                entities.ResourceCard.GOLD: 2,
                entities.ResourceCard.WOOD: 2,
            }
        ),
        rng_=action.rng_,
    )


def test_timeout_play_mamo_returns_explicit_resource(
    game: entities.ActiveGame,
) -> None:
    action = timeouts.timeout_play_mamo(game, random.Random(0))

    assert action == actions.PlayMamoAction(
        by="player-0",
        resource=entities.ResourceCard.MAIZE,
        rng_=action.rng_,
    )


def test_timeout_play_blessed_samples_from_supply(
    game: entities.ActiveGame,
) -> None:
    action = timeouts.timeout_play_blessed(game, random.Random(0))

    assert action == actions.PlayBlessedAction(
        by="player-0",
        resources=(entities.ResourceCard.COTTON, entities.ResourceCard.COTTON),
        rng_=action.rng_,
    )


def test_timeout_play_blessed_falls_back_when_supply_too_small(
    game: entities.ActiveGame,
) -> None:
    game.resource_supply = collections.Counter()

    action = timeouts.timeout_play_blessed(game, random.Random(0))

    assert action == actions.PlayBlessedAction(
        by="player-0",
        resources=(entities.ResourceCard.GOLD, entities.ResourceCard.STONE),
        rng_=action.rng_,
    )


def test_timeout_play_pathfinder_returns_empty_when_no_legal_paths(
    game: entities.ActiveGame,
) -> None:
    action = timeouts.timeout_play_pathfinder(game, random.Random(0))

    assert action == actions.PlayPathfinderAction(
        by="player-0",
        paths=(),
        rng_=action.rng_,
    )


def test_timeout_play_pathfinder_returns_explicit_paths(
    game: entities.ActiveGame,
) -> None:
    game.use_vertex(
        "player-0",
        entities.canonical_vertex(0, 0, 0),
        entities.SettlementType.TERRACE,
    )

    action = timeouts.timeout_play_pathfinder(game, random.Random(0))

    assert action == actions.PlayPathfinderAction(
        by="player-0",
        paths=(
            entities.Coordinate(q=0, r=-1, d=1),
            entities.Coordinate(q=0, r=-1, d=2),
        ),
        rng_=action.rng_,
    )


def _multi_hex_game() -> entities.ActiveGame:
    nicknames = ("player-0", "player-1", "player-2")
    return entities.ActiveGame(
        map=(
            entities.Hex(q=0, r=0, type=entities.HexType.DESERT, number=7),
            entities.Hex(q=1, r=0, type=entities.HexType.MOUNTAINS, number=6),
            entities.Hex(q=0, r=1, type=entities.HexType.JUNGLE, number=5),
        ),
        conquistator_location=entities.HexLocation(q=0, r=0),
        turn_order=nicknames,
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
    )
