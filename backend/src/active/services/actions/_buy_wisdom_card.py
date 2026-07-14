from .... import player
from ... import entities
from . import _errors


def buy_wisdom_card(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
) -> None:
    if not game.wisdom_deck:
        raise _errors.EmptyWisdomDeck

    resources = game.players[to].resources
    if resources[entities.ResourceCard.GOLD] < 1:
        raise _errors.InsufficientResources
    if resources[entities.ResourceCard.COTTON] < 1:
        raise _errors.InsufficientResources
    if resources[entities.ResourceCard.MAIZE] < 1:
        raise _errors.InsufficientResources

    game.players[to].resources.update(
        {
            entities.ResourceCard.GOLD: -1,
            entities.ResourceCard.COTTON: -1,
            entities.ResourceCard.MAIZE: -1,
        }
    )
    game.resource_supply.update(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    card = game.wisdom_deck.pop()
    game.players[to].cards[card] += 1
