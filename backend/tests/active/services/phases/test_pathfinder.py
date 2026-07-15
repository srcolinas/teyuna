import pytest

from src.active import entities
from src.active.services import actions, phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[1],
                action=phases.BuyAction(
                    item=phases.Buyable.PATH,
                    coordinate=entities.Coordinate(q=0, r=0, d=0),
                ),
            ),
        )


def test_raises_invalid_action_if_not_allowed(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.PlayWisdomCardAction(card=entities.WisdomCard.PATHFINDER),
            ),
        )


def test_rejects_non_path_buy_action(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.BuyAction(
                    item=phases.Buyable.TERRACE,
                    coordinate=entities.Coordinate(q=0, r=0, d=0),
                ),
            ),
        )


def test_two_paths_finish_phase(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    active = game.active_player
    actions.add_free_terrace(game, active, q=0, r=0, direction=0)
    phase.on_enter(game)

    first = phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.BuyAction(
                item=phases.Buyable.PATH,
                coordinate=entities.Coordinate(q=0, r=0, d=0),
            ),
        ),
    )
    second = phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.BuyAction(
                item=phases.Buyable.PATH,
                coordinate=entities.Coordinate(q=0, r=0, d=1),
            ),
        ),
    )

    assert first == phases.RunOutcome(finished=False, value=None)
    assert second == phases.RunOutcome(finished=True, value=None)
    assert entities.canonical_edge(0, 0, 0) in game.players[active].paths
    assert entities.canonical_edge(0, 0, 1) in game.players[active].paths


def test_invalid_path_location_raises(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    phase.on_enter(game)
    with pytest.raises(actions.InvalidPathLocation):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.BuyAction(
                    item=phases.Buyable.PATH,
                    coordinate=entities.Coordinate(q=0, r=0, d=0),
                ),
            ),
        )


def test_rejects_when_no_paths_available(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    active = game.active_player
    actions.add_free_terrace(game, active, q=0, r=0, direction=0)
    for edge in list(game.free_edges)[: entities.MAX_PATHS]:
        game.players[active].paths.add(edge)
        game.free_edges.remove(edge)
    phase.on_enter(game)

    with pytest.raises(actions.InsufficientResources):
        phase.run(
            game,
            phases.PlayerRequest(
                by=active,
                action=phases.BuyAction(
                    item=phases.Buyable.PATH,
                    coordinate=entities.Coordinate(q=0, r=0, d=0),
                ),
            ),
        )


def test_advance_phase_finishes_early(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    active = game.active_player
    actions.add_free_terrace(game, active, q=0, r=0, direction=0)
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.BuyAction(
                item=phases.Buyable.PATH,
                coordinate=entities.Coordinate(q=0, r=0, d=0),
            ),
        ),
    )

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.AdvancePhaseAction(),
        ),
    )

    assert result == phases.RunOutcome(finished=True, value=None)
    assert len(game.players[active].paths) == 1


def test_path_can_award_longest_road(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    active = game.active_player
    player = game.players[active]
    for d in range(4):
        edge = entities.canonical_edge(0, 0, d)
        player.paths.add(edge)
        game.free_edges.discard(edge)
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.BuyAction(
                item=phases.Buyable.PATH,
                coordinate=entities.Coordinate(q=0, r=0, d=4),
            ),
        ),
    )

    assert result == phases.RunOutcome(
        finished=False,
        value=phases.LongestRoadResult(owner=active, length=5),
    )
    assert game.longest_road == (active, 5)


def test_on_exit_returns_to_pathfinder_return_phase(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    game.pathfinder_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert game.pathfinder_return_phase is None


def test_on_exit_returns_to_trade_and_build_when_set(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    game.pathfinder_return_phase = phases.GamePhaseName.TRADE_AND_BUILD.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.TRADE_AND_BUILD
    assert game.pathfinder_return_phase is None


def test_path_declares_winner_via_longest_road(
    game: entities.ActiveGame,
    phase: phases.PathfinderPhase,
) -> None:
    active = game.active_player
    player = game.players[active]
    player.played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 8
    for d in range(4):
        edge = entities.canonical_edge(0, 0, d)
        player.paths.add(edge)
        game.free_edges.discard(edge)
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    game.pathfinder_return_phase = phases.GamePhaseName.TRADE_AND_BUILD.value
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.BuyAction(
                item=phases.Buyable.PATH,
                coordinate=entities.Coordinate(q=0, r=0, d=4),
            ),
        ),
    )

    assert result == phases.RunOutcome(
        finished=True, value=phases.GameWonResult(winner=active)
    )
    assert game.winner == active
    assert game.longest_road == (active, 5)
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.END
    assert game.pathfinder_return_phase is None


@pytest.fixture
def phase() -> phases.PathfinderPhase:
    return phases.PathfinderPhase()
