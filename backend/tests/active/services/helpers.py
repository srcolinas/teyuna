import collections

from src import player
from src.active import entities


def setup_construction_phase(game: entities.ActiveGame) -> None:
    game.set_game_phase(entities.GamePhase.MAIN)
    game.set_turn_phase(entities.TurnPhase.CONSTRUCTION)


def fund_path_purchase(
    game: entities.ActiveGame, nickname: player.Nickname, *, count: int = 1
) -> None:
    game.grant_resources(
        nickname,
        resources=collections.Counter(
            {
                entities.ResourceCard.STONE: count,
                entities.ResourceCard.WOOD: count,
            }
        ),
    )


def fund_terrace_purchase(
    game: entities.ActiveGame, nickname: player.Nickname, *, count: int = 1
) -> None:
    game.grant_resources(
        nickname,
        resources=collections.Counter(
            {
                entities.ResourceCard.STONE: count,
                entities.ResourceCard.WOOD: count,
                entities.ResourceCard.COTTON: count,
                entities.ResourceCard.MAIZE: count,
            }
        ),
    )
