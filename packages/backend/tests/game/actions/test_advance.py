import collections
import datetime
import random

from src.game import actions, entities
from src.game.actions.handlers import _advance
import teyuna_core


def test_handle_advance_first_placement(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.FIRST_PLACEMENT
    player = game.active_player

    result = actions.handle_advance(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        teyuna_core.PlayerAction(),
    )

    assert result.error is None
    assert isinstance(result, teyuna_core.PlacedBuildingsResult)
    assert result.action.kind == "free_placement"
    assert result.settlement is not None
    assert result.path is not None
    assert result.settlement in teyuna_core.vertices_of_edge(result.path)


def test_handle_advance_move_conquistator() -> None:
    game = _multi_hex_game()
    game.phase = teyuna_core.GamePhaseName.MOVE_CONQUISTATOR
    player = game.active_player

    result = actions.handle_advance(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        teyuna_core.PlayerAction(),
    )

    assert result.error is None
    assert isinstance(result, teyuna_core.MovedConquistatorResult)
    assert result.action.kind == "move_conquistator"
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert game.conquistator_location != teyuna_core.HexLocation(q=0, r=0)


def test_resolve_free_placement_path_always_touches_new_terrace(
    game: entities.Game,
) -> None:
    player = game.active_player
    first_terrace = teyuna_core.canonical_vertex(0, 0, 0)
    first_path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    game.use_vertex(player, first_terrace, teyuna_core.SettlementType.TERRACE)
    game.use_edge(player, first_path)

    for seed in range(20):
        action = _advance.resolve_free_placement(
            game,
            actions.ExecutionContext(
                by=player,
                due_to_timeout=False,
                rng=random.Random(seed),
            ),
            teyuna_core.FreePlacementAction(),
        )
        assert action.terrace is not None
        assert action.path is not None
        assert action.terrace in teyuna_core.vertices_of_edge(action.path)
        assert action.terrace != first_terrace


def test_discard_resources_for_uses_submitting_player(game: entities.Game) -> None:
    game.players["player-0"].resources = collections.Counter(
        {teyuna_core.ResourceCard.WOOD: 4}
    )
    game.players["player-1"].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 6}
    )
    game.to_discard_resources = {"player-0": 2, "player-1": 3}

    action = _advance.discard_resources_for(
        game,
        actions.ExecutionContext(
            by="player-1",
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        teyuna_core.DiscardResourcesAction(count={}),
    )

    assert sum(action.count.values()) == 3


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
