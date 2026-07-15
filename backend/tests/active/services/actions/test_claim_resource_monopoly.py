import collections
import random
from typing import Any

from src.active import entities
from src.active.services import actions


def test_claims_resource_from_all_opponents(game: entities.ActiveGame) -> None:
    active = game.active_player
    opponent_a = game.turn_order[1]
    opponent_b = game.turn_order[2]
    game.players[opponent_a].resources[entities.ResourceCard.GOLD] = 3
    game.players[opponent_b].resources[entities.ResourceCard.GOLD] = 2
    game.players[active].resources[entities.ResourceCard.GOLD] = 1

    taken = actions.claim_resource_monopoly(
        game, active, resource=entities.ResourceCard.GOLD
    )

    assert taken == collections.Counter({entities.ResourceCard.GOLD: 5})
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 6
    assert game.players[opponent_a].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[opponent_b].resources[entities.ResourceCard.GOLD] == 0


def test_claim_leaves_other_resources_untouched(game: entities.ActiveGame) -> None:
    active = game.active_player
    opponent = game.turn_order[1]
    game.players[opponent].resources[entities.ResourceCard.GOLD] = 2
    game.players[opponent].resources[entities.ResourceCard.WOOD] = 4

    actions.claim_resource_monopoly(game, active, resource=entities.ResourceCard.GOLD)

    assert game.players[opponent].resources[entities.ResourceCard.WOOD] == 4
    assert game.players[active].resources[entities.ResourceCard.WOOD] == 0


def test_claim_with_no_matching_resources_is_noop(game: entities.ActiveGame) -> None:
    active = game.active_player

    taken = actions.claim_resource_monopoly(
        game, active, resource=entities.ResourceCard.STONE
    )

    assert taken == collections.Counter()
    assert game.players[active].resources[entities.ResourceCard.STONE] == 0


def test_claim_randomly_uses_chosen_resource(game: entities.ActiveGame) -> None:
    active = game.active_player
    opponent = game.turn_order[1]
    game.players[opponent].resources[entities.ResourceCard.COTTON] = 3
    rnd = _FixedChoiceRandom(entities.ResourceCard.COTTON)

    taken = actions.claim_resource_monopoly_randomly(game, active, rnd=rnd)

    assert taken == collections.Counter({entities.ResourceCard.COTTON: 3})
    assert game.players[active].resources[entities.ResourceCard.COTTON] == 3


class _FixedChoiceRandom(random.Random):
    def __init__(self, choice: entities.ResourceCard) -> None:
        super().__init__()
        self._choice = choice

    def choice(self, seq: Any) -> Any:
        del seq
        return self._choice
