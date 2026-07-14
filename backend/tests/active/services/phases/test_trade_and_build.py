import collections
import uuid

import pytest

from src.active import entities
from src.active.services import phases


def test_active_player_cannot_propose_trade(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter({entities.ResourceCard.GOLD: 1})
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.ProposeTradeToPlayerInTurnAction(
                    offer=collections.Counter({entities.ResourceCard.GOLD: 1}),
                    request=collections.Counter({entities.ResourceCard.STONE: 1}),
                ),
            ),
        )


def test_non_active_player_can_propose_trade(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    proposer = game.turn_order[1]
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=proposer,
            action=phases.ProposeTradeToPlayerInTurnAction(
                offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                request=collections.Counter({entities.ResourceCard.STONE: 1}),
            ),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert len(game.trade_proposals) == 1


@pytest.mark.parametrize(
    "action",
    [
        phases.TradeWithSupplyAction(
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        ),
        phases.AcceptTradeProposalAction(id=uuid.uuid4()),
        phases.BuyAction(
            item=phases.Buyable.PATH,
            coordinate=entities.Coordinate(q=0, r=0, d=0),
        ),
        phases.BuyWisdomCardAction(),
        phases.AdvancePhaseAction(),
    ],
)
def test_non_active_player_cannot_perform_active_actions(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
    action: phases.PlayerAction,
) -> None:
    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(by=game.turn_order[1], action=action),
        )


def test_raises_invalid_action_if_not_allowed(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
            ),
        )


def test_trade_with_supply_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter({entities.ResourceCard.GOLD: 4})
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.TradeWithSupplyAction(
                offers=entities.ResourceCard.GOLD,
                requests=entities.ResourceCard.STONE,
            ),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert player.resources[entities.ResourceCard.GOLD] == 0
    assert player.resources[entities.ResourceCard.STONE] == 1


def test_accept_trade_returns_proposal(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    proposal_id = uuid.uuid4()
    proposer = game.turn_order[1]
    proposal = entities.TradeProposal(
        by=proposer,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    game.trade_proposals = {proposal_id: proposal}
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AcceptTradeProposalAction(id=proposal_id),
        ),
    )

    assert result == phases.RunOutcome(finished=False, value=proposal)
    assert game.trade_proposals == {}


def test_buy_path_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources = collections.Counter(
        {entities.ResourceCard.STONE: 1, entities.ResourceCard.WOOD: 1}
    )
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.BuyAction(
                item=phases.Buyable.PATH,
                coordinate=entities.Coordinate(q=0, r=0, d=0),
            ),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert entities.canonical_edge(0, 0, 0) in player.paths


def test_buy_terrace_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources = collections.Counter(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.BuyAction(
                item=phases.Buyable.TERRACE,
                coordinate=entities.Coordinate(q=0, r=0, d=2),
            ),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert entities.canonical_vertex(0, 0, 2) in player.settlements


def test_buy_great_terrace_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources = collections.Counter(
        {entities.ResourceCard.GOLD: 3, entities.ResourceCard.MAIZE: 2}
    )
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.BuyAction(
                item=phases.Buyable.GREAT_TERRACE,
                coordinate=entities.Coordinate(q=0, r=0, d=0),
            ),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert (
        player.settlements[entities.canonical_vertex(0, 0, 0)]
        is entities.SettlementType.GREAT_TERRACE
    )


def test_buy_wisdom_card_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    game.wisdom_deck = [entities.WisdomCard.WARRIOR]
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.BuyWisdomCardAction(),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert player.cards[entities.WisdomCard.WARRIOR] == 1


def test_advance_phase_finishes(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )
    assert result == phases.RunOutcome(finished=True, value=None)


def test_on_enter_clears_trade_proposals(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    game.trade_proposals = {
        uuid.uuid4(): entities.TradeProposal(
            by=game.turn_order[1],
            offer=collections.Counter({entities.ResourceCard.GOLD: 1}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        )
    }
    phase.on_enter(game)
    assert game.trade_proposals == {}


def test_on_exit_clears_trade_proposals_and_advances_player(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    game.player_idx = 0
    game.trade_proposals = {
        uuid.uuid4(): entities.TradeProposal(
            by=game.turn_order[1],
            offer=collections.Counter({entities.ResourceCard.GOLD: 1}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        )
    }
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert game.player_idx == 1
    assert game.trade_proposals == {}


def test_on_exit_wraps_player_idx_to_first(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    game.player_idx = len(game.turn_order) - 1
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert game.player_idx == 0


@pytest.fixture
def phase() -> phases.TradeAndBuildPhase:
    return phases.TradeAndBuildPhase()
