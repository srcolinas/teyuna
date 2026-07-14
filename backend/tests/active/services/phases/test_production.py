import pytest

from src.active import entities
from src.active.services import phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.ProductionPhase,
) -> None:
    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[1],
                action=phases.AdvancePhaseAction(),
            ),
        )


def test_raises_invalid_action_if_not_allowed(
    game: entities.ActiveGame,
    phase: phases.ProductionPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
            ),
        )


def test_advance_phase_finishes(
    game: entities.ActiveGame,
    phase: phases.ProductionPhase,
) -> None:
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )
    assert result == phases.RunOutcome(finished=True, value=None)


def test_on_enter_produces_resources_from_last_dice_roll(
    game: entities.ActiveGame,
    phase: phases.ProductionPhase,
) -> None:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=8)
    desert = entities.Hex(q=0, r=1, type=entities.HexType.DESERT, number=7)
    game.map = (mountains, desert)
    game.conquistator_location = desert
    game.last_dice_roll = 8
    game.players[game.active_player].settlements = entities.SettlementsCollection(
        {
            entities.Coordinate(q=0, r=-1, d=2): entities.SettlementType.TERRACE,
        },
    )
    phase.on_enter(game)
    assert game.players[game.active_player].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_on_exit_returns_trade_and_build_phase(
    game: entities.ActiveGame,
    phase: phases.ProductionPhase,
) -> None:
    assert phase.on_exit(game).next is phases.GamePhaseName.TRADE_AND_BUILD


@pytest.fixture
def phase() -> phases.ProductionPhase:
    return phases.ProductionPhase()
