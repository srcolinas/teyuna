import pytest

from src.active import entities
from src.active.services import phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    phase.on_enter(game)

    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[1],
                action=phases.AddInitialBuildingsAction(
                    terrace=entities.Coordinate(q=0, r=0, d=0),
                    path=entities.Coordinate(q=0, r=0, d=0),
                ),
            ),
        )


def test_raises_invalid_action_if_not_add_initial_buildings_action(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    phase.on_enter(game)
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


def test_run_increases_player_idx_by_1(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    game.player_idx = 0
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AddInitialBuildingsAction(
                terrace=entities.Coordinate(q=0, r=0, d=0),
                path=entities.Coordinate(q=0, r=0, d=0),
            ),
        ),
    )
    assert game.player_idx == 1


def test_returns_false_before_last_player_has_added_initial_buildings(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    game.player_idx = 0
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AddInitialBuildingsAction(
                terrace=entities.Coordinate(q=0, r=0, d=0),
                path=entities.Coordinate(q=0, r=0, d=0),
            ),
        ),
    )
    assert result.finished is False


def test_returns_true_after_last_player_has_added_initial_buildings(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    game.player_idx = len(game.players) - 1
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AddInitialBuildingsAction(
                terrace=entities.Coordinate(q=0, r=0, d=0),
                path=entities.Coordinate(q=0, r=0, d=0),
            ),
        ),
    )
    assert result.finished is True


def test_on_exit_returns_second_placement_phase(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    phase.on_enter(game)
    assert phase.on_exit(game).next is phases.GamePhaseName.SECOND_PLACEMENT


def test_on_enter_sets_player_idx_to_0(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    phase.on_enter(game)
    assert game.player_idx == 0


def test_on_exit_assigns_player_idx_to_last_player(
    game: entities.ActiveGame,
    phase: phases.FirstPlacementPhase,
) -> None:
    phase.on_enter(game)
    phase.on_exit(game)
    assert game.player_idx == len(game.players) - 1


@pytest.fixture
def phase() -> phases.FirstPlacementPhase:
    return phases.FirstPlacementPhase()
