import collections
import uuid

import pytest

from src.active import entities, services


@pytest.mark.parametrize(
    "phase", [entities.GamePhase.INITIAL, entities.GamePhase.FINISHED]
)
def test_cannot_propose_if_not_in_main_phase(
    phase: entities.GamePhase, game: entities.ActiveGame
) -> None:
    game.phase = phase
    with pytest.raises(
        services.InvalidGamePhase,
        match="Trade proposals can only be made in the main phase.",
    ):
        services.propose_trade(
            game,
            by=game.turn_order[0],
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        )


@pytest.mark.parametrize(
    "phase", [entities.TurnPhase.PRODUCTION, entities.TurnPhase.CONSTRUCTION]
)
def test_cannot_propose_if_not_in_trade_phase(
    phase: entities.TurnPhase, game: entities.ActiveGame
) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = phase
    with pytest.raises(
        services.InvalidTurnPhase,
        match="Trade proposals can only be made in the trade phase.",
    ):
        services.propose_trade(
            game,
            by=game.turn_order[0],
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        )


def test_propose_trade_returns_id(game: entities.ActiveGame) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    nickname = game.turn_order[0]
    services.grant_resources(
        game, nickname, resources=collections.Counter({entities.ResourceCard.GOLD: 2})
    )
    id = services.propose_trade(
        game,
        by=nickname,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    assert isinstance(id, uuid.UUID)


def test_cannot_propose_if_not_enough_resources(game: entities.ActiveGame) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    with pytest.raises(
        services.InsufficientResources, match="You do not have enough gold to offer."
    ):
        services.propose_trade(
            game,
            by=game.turn_order[1],
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        )


def test_propose_trade_is_added_to_trade_proposals(game: entities.ActiveGame) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    nickname = game.turn_order[0]
    services.grant_resources(
        game, nickname, resources=collections.Counter({entities.ResourceCard.GOLD: 2})
    )
    id = services.propose_trade(
        game,
        by=nickname,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    assert game.trade_proposals == {
        id: entities.TradeProposal(
            by=nickname,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        ),
    }
