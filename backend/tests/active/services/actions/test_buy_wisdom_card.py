import pytest

from src.active import entities
from src.active.services import actions

_WISDOM_CARD_COST = {
    entities.ResourceCard.GOLD: 1,
    entities.ResourceCard.COTTON: 1,
    entities.ResourceCard.MAIZE: 1,
}


def test_cannot_buy_wisdom_card_with_insufficient_resources(
    game: entities.ActiveGame,
) -> None:
    game.wisdom_deck = [entities.WisdomCard.WARRIOR]
    game.players[game.active_player].resources.update(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    with pytest.raises(actions.InsufficientResources):
        actions.buy_wisdom_card(game, game.active_player)


def test_cannot_buy_wisdom_card_when_deck_is_empty(
    game: entities.ActiveGame,
) -> None:
    game.wisdom_deck = []
    game.players[game.active_player].resources.update(_WISDOM_CARD_COST)
    with pytest.raises(actions.EmptyWisdomDeck):
        actions.buy_wisdom_card(game, game.active_player)


def test_buy_wisdom_card_updates_player_cards_resources_supply_and_deck(
    game: entities.ActiveGame,
) -> None:
    card = entities.WisdomCard.WARRIOR
    game.wisdom_deck = [card]
    player = game.players[game.active_player]
    player.resources.update(_WISDOM_CARD_COST)
    supply_before = {
        entities.ResourceCard.GOLD: game.resource_supply[entities.ResourceCard.GOLD],
        entities.ResourceCard.COTTON: game.resource_supply[
            entities.ResourceCard.COTTON
        ],
        entities.ResourceCard.MAIZE: game.resource_supply[entities.ResourceCard.MAIZE],
    }

    actions.buy_wisdom_card(game, game.active_player)

    assert player.cards[card] == 1
    assert player.resources[entities.ResourceCard.GOLD] == 0
    assert player.resources[entities.ResourceCard.COTTON] == 0
    assert player.resources[entities.ResourceCard.MAIZE] == 0
    assert game.wisdom_deck == []
    assert (
        game.resource_supply[entities.ResourceCard.GOLD]
        == supply_before[entities.ResourceCard.GOLD] + 1
    )
    assert (
        game.resource_supply[entities.ResourceCard.COTTON]
        == supply_before[entities.ResourceCard.COTTON] + 1
    )
    assert (
        game.resource_supply[entities.ResourceCard.MAIZE]
        == supply_before[entities.ResourceCard.MAIZE] + 1
    )
