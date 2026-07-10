import collections
import uuid

import pytest

from src.active import entities, services


@pytest.mark.parametrize(
    "phase", [entities.GamePhase.INITIAL, entities.GamePhase.FINISHED]
)
def test_cannot_accept_trade_if_not_in_main_phase(
    phase: entities.GamePhase, game: entities.ActiveGame
) -> None:
    game.phase = phase
    game.turn_phase = entities.TurnPhase.TRADE
    with pytest.raises(
        services.InvalidGamePhase,
        match="Trade proposals can only be accepted in the main phase.",
    ):
        services.accept_trade(
            game,
            by=game.turn_order[0],
            id=uuid.uuid4(),
        )


@pytest.mark.parametrize(
    "phase", [entities.TurnPhase.PRODUCTION, entities.TurnPhase.CONSTRUCTION]
)
def test_cannot_accept_trade_if_not_in_trade_phase(
    phase: entities.TurnPhase, game: entities.ActiveGame
) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = phase
    with pytest.raises(
        services.InvalidTurnPhase,
        match="Trade proposals can only be accepted in the trade phase.",
    ):
        services.accept_trade(
            game,
            by=game.turn_order[0],
            id=uuid.uuid4(),
        )


def test_cannot_accept_trade_if_not_in_turn(game: entities.ActiveGame) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    with pytest.raises(services.PlayerNotInTurn):
        services.accept_trade(
            game,
            by=game.turn_order[1],
            id=uuid.uuid4(),
        )


def test_cannot_accept_if_not_in_trade_proposals(game: entities.ActiveGame) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    id = uuid.uuid4()
    with pytest.raises(
        services.TradeProposalNotFound,
        match=f"Trade proposal {id} not found.",
    ):
        services.accept_trade(
            game,
            by=game.turn_order[0],
            id=id,
        )


def test_cannot_accept_if_not_enough_resources(game: entities.ActiveGame) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    proposes = game.turn_order[1]
    services.grant_resources(
        game, proposes, resources=collections.Counter({entities.ResourceCard.GOLD: 2})
    )
    id = services.propose_trade(
        game,
        by=proposes,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    with pytest.raises(
        services.InsufficientResources,
        match="You do not have enough stone to accept the trade.",
    ):
        services.accept_trade(
            game,
            by=game.turn_order[0],
            id=id,
        )


def test_accepted_trade_is_removed_from_trade_proposals(
    game: entities.ActiveGame,
) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    proposes = game.turn_order[1]
    accepts = game.turn_order[0]
    services.grant_resources(
        game, proposes, resources=collections.Counter({entities.ResourceCard.GOLD: 2})
    )
    services.grant_resources(
        game, accepts, resources=collections.Counter({entities.ResourceCard.STONE: 1})
    )
    id = services.propose_trade(
        game,
        by=proposes,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    services.accept_trade(
        game,
        by=accepts,
        id=id,
    )
    assert game.trade_proposals == {}


def test_accepted_trade_changes_proposer_resources(
    game: entities.ActiveGame,
) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    proposes = game.turn_order[1]
    accepts = game.turn_order[0]
    services.grant_resources(
        game, proposes, resources=collections.Counter({entities.ResourceCard.GOLD: 2})
    )
    services.grant_resources(
        game, accepts, resources=collections.Counter({entities.ResourceCard.STONE: 1})
    )
    id = services.propose_trade(
        game,
        by=proposes,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    services.accept_trade(
        game,
        by=accepts,
        id=id,
    )
    assert game.players[proposes].resources == collections.Counter(
        {entities.ResourceCard.GOLD: 0, entities.ResourceCard.STONE: 1}
    )


def test_accepted_trade_changes_acceptor_resources(
    game: entities.ActiveGame,
) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.TRADE
    proposes = game.turn_order[1]
    accepts = game.turn_order[0]
    services.grant_resources(
        game, proposes, resources=collections.Counter({entities.ResourceCard.GOLD: 2})
    )
    services.grant_resources(
        game, accepts, resources=collections.Counter({entities.ResourceCard.STONE: 1})
    )
    id = services.propose_trade(
        game,
        by=proposes,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    services.accept_trade(
        game,
        by=accepts,
        id=id,
    )
    assert game.players[accepts].resources == collections.Counter(
        {entities.ResourceCard.GOLD: 2, entities.ResourceCard.STONE: 0}
    )
