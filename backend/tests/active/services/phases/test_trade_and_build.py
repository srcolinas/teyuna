import collections
import uuid

import pytest

from src.active import entities
from src.active.services import actions, phases


def test_active_player_can_propose_trade_to_others(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter({entities.ResourceCard.GOLD: 2})
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.ProposeTradeAction(
                offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                request=collections.Counter({entities.ResourceCard.STONE: 1}),
                to=(game.turn_order[1], game.turn_order[2]),
            ),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert len(game.trade_proposals) == 1
    proposal = next(iter(game.trade_proposals.values()))
    assert proposal.to == (game.turn_order[1], game.turn_order[2])


def test_non_active_player_can_propose_trade_to_active(
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
            action=phases.ProposeTradeAction(
                offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                request=collections.Counter({entities.ResourceCard.STONE: 1}),
                to=(game.active_player,),
            ),
        ),
    )
    assert result == phases.RunOutcome(finished=False, value=None)
    assert len(game.trade_proposals) == 1


def test_non_active_player_cannot_propose_to_non_active(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    proposer = game.turn_order[1]
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=proposer,
                action=phases.ProposeTradeAction(
                    offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                    request=collections.Counter({entities.ResourceCard.STONE: 1}),
                    to=(game.turn_order[2],),
                ),
            ),
        )


def test_empty_trade_targets_raises(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter({entities.ResourceCard.GOLD: 2})
    with pytest.raises(actions.InvalidTradeTargets):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.ProposeTradeAction(
                    offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                    request=collections.Counter({entities.ResourceCard.STONE: 1}),
                    to=(),
                ),
            ),
        )


@pytest.mark.parametrize(
    "action",
    [
        phases.TradeWithSupplyAction(
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        ),
        phases.BuyAction(
            item=phases.Buyable.PATH,
            coordinate=entities.Coordinate(q=0, r=0, d=0),
        ),
        phases.BuyWisdomCardAction(),
        phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
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
                action=phases.MoveConquistatorAction(q=0, r=0),
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


def test_active_player_can_accept_trade(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    proposal_id = uuid.uuid4()
    proposer = game.turn_order[1]
    proposal = entities.TradeProposal(
        by=proposer,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
        to=(game.active_player,),
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


def test_directed_non_active_can_accept_trade(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    proposal_id = uuid.uuid4()
    acceptor = game.turn_order[1]
    proposal = entities.TradeProposal(
        by=game.active_player,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
        to=(acceptor, game.turn_order[2]),
    )
    game.trade_proposals = {proposal_id: proposal}
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[acceptor].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=acceptor,
            action=phases.AcceptTradeProposalAction(id=proposal_id),
        ),
    )

    assert result == phases.RunOutcome(finished=False, value=proposal)
    assert game.trade_proposals == {}


def test_acceptor_not_in_to_raises(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    proposal_id = uuid.uuid4()
    game.trade_proposals = {
        proposal_id: entities.TradeProposal(
            by=game.active_player,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=(game.turn_order[1],),
        )
    }
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[game.turn_order[2]].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[2],
                action=phases.AcceptTradeProposalAction(id=proposal_id),
            ),
        )


def test_first_acceptor_wins_among_multiple_recipients(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    proposal_id = uuid.uuid4()
    first = game.turn_order[1]
    second = game.turn_order[2]
    proposal = entities.TradeProposal(
        by=game.active_player,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
        to=(first, second),
    )
    game.trade_proposals = {proposal_id: proposal}
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[first].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )
    game.players[second].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )

    phase.run(
        game,
        phases.PlayerRequest(
            by=first,
            action=phases.AcceptTradeProposalAction(id=proposal_id),
        ),
    )
    assert game.trade_proposals == {}

    with pytest.raises(actions.TradeProposalNotFound):
        phase.run(
            game,
            phases.PlayerRequest(
                by=second,
                action=phases.AcceptTradeProposalAction(id=proposal_id),
            ),
        )


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


def test_buy_path_awards_longest_road(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    for d in range(4):
        edge = entities.canonical_edge(0, 0, d)
        player.paths.add(edge)
        game.free_edges.discard(edge)
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
                coordinate=entities.Coordinate(q=0, r=0, d=4),
            ),
        ),
    )

    assert result == phases.RunOutcome(
        finished=False,
        value=phases.LongestRoadResult(owner=game.active_player, length=5),
    )
    assert game.longest_road == (game.active_player, 5)


def test_buy_path_same_owner_length_growth_does_not_report(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    for d in range(5):
        edge = entities.canonical_edge(0, 0, d)
        player.paths.add(edge)
        game.free_edges.discard(edge)
    game.longest_road = (game.active_player, 5)
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
                coordinate=entities.Coordinate(q=0, r=0, d=5),
            ),
        ),
    )

    assert result == phases.RunOutcome(finished=False, value=None)
    assert game.longest_road == (game.active_player, 6)


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


def test_buy_terrace_with_longest_road_break_reports_clear(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    _place_paths(
        game,
        holder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0)],
    )
    actions.add_free_terrace(game, breaker, q=-2, r=2, direction=1)
    actions.add_free_path(game, breaker, q=-1, r=1, direction=2)
    actions.add_free_path(game, breaker, q=-1, r=1, direction=1)
    game.longest_road = (holder, 6)
    game.players[breaker].resources = collections.Counter(
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
            by=breaker,
            action=phases.BuyAction(
                item=phases.Buyable.TERRACE,
                coordinate=entities.Coordinate(q=0, r=0, d=3),
            ),
        ),
    )

    assert result == phases.RunOutcome(
        finished=False,
        value=phases.LongestRoadResult(owner=None, length=0),
    )
    assert game.longest_road == (None, 0)


def test_buy_terrace_with_longest_road_no_break_leaves_award(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    game.longest_road = (holder, 5)
    _place_paths(game, breaker, [(0, 0, 0), (0, 0, 1)])
    game.players[breaker].resources = collections.Counter(
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
            by=breaker,
            action=phases.BuyAction(
                item=phases.Buyable.TERRACE,
                coordinate=entities.Coordinate(q=0, r=0, d=2),
            ),
        ),
    )

    assert result == phases.RunOutcome(finished=False, value=None)
    assert game.longest_road == (holder, 5)


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


def test_play_warrior_finishes_phase(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.WARRIOR] = 1
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
        ),
    )
    assert result == phases.RunOutcome(finished=True, value=entities.WisdomCard.WARRIOR)
    assert player.played_cards[entities.WisdomCard.WARRIOR] == 1
    assert game.warrior_return_phase == phases.GamePhaseName.TRADE_AND_BUILD.value


def test_play_blessing_finishes_phase(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.BLESSING_OF_ALUNA] = 1
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(
                card=entities.WisdomCard.BLESSING_OF_ALUNA
            ),
        ),
    )
    assert result == phases.RunOutcome(
        finished=True, value=entities.WisdomCard.BLESSING_OF_ALUNA
    )
    assert player.played_cards[entities.WisdomCard.BLESSING_OF_ALUNA] == 1
    assert game.blessing_return_phase == phases.GamePhaseName.TRADE_AND_BUILD.value


def test_play_non_interrupt_wisdom_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.PATHFINDER] = 1
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(card=entities.WisdomCard.PATHFINDER),
        ),
    )
    assert result == phases.RunOutcome(
        finished=False, value=entities.WisdomCard.PATHFINDER
    )
    assert player.played_cards[entities.WisdomCard.PATHFINDER] == 1
    assert game.warrior_return_phase is None
    assert game.blessing_return_phase is None


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
            to=(game.active_player,),
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
            to=(game.active_player,),
        )
    }
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert game.player_idx == 1
    assert game.trade_proposals == {}


def test_on_exit_after_warrior_goes_to_warrior_move_without_rotating(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.WARRIOR] = 1
    game.player_idx = 0
    game.trade_proposals = {
        uuid.uuid4(): entities.TradeProposal(
            by=game.turn_order[1],
            offer=collections.Counter({entities.ResourceCard.GOLD: 1}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=(game.active_player,),
        )
    }
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
        ),
    )
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.WARRIOR_MOVE_CONQUISTATOR
    assert game.player_idx == 0
    assert len(game.trade_proposals) == 1


def test_on_exit_after_blessing_goes_to_blessing_without_rotating(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.BLESSING_OF_ALUNA] = 1
    game.player_idx = 0
    game.trade_proposals = {
        uuid.uuid4(): entities.TradeProposal(
            by=game.turn_order[1],
            offer=collections.Counter({entities.ResourceCard.GOLD: 1}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=(game.active_player,),
        )
    }
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(
                card=entities.WisdomCard.BLESSING_OF_ALUNA
            ),
        ),
    )
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.BLESSING_OF_ALUNA
    assert game.player_idx == 0
    assert len(game.trade_proposals) == 1


def test_on_exit_wraps_player_idx_to_first(
    game: entities.ActiveGame,
    phase: phases.TradeAndBuildPhase,
) -> None:
    game.player_idx = len(game.turn_order) - 1
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert game.player_idx == 0


def _place_paths(
    game: entities.ActiveGame,
    nickname: str,
    edges: list[tuple[int, int, int]],
    *,
    terrace: tuple[int, int, int] | None = None,
) -> None:
    if terrace is None:
        terrace = edges[0]
    tq, tr, td = terrace
    actions.add_free_terrace(game, nickname, q=tq, r=tr, direction=td)
    for q, r, d in edges:
        actions.add_free_path(game, nickname, q=q, r=r, direction=d)


@pytest.fixture
def phase() -> phases.TradeAndBuildPhase:
    return phases.TradeAndBuildPhase()
