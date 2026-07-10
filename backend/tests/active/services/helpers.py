import collections

from src import player
from src.active import entities, services


def setup_construction_phase(game: entities.ActiveGame) -> None:
    game.phase = entities.GamePhase.MAIN
    game.turn_phase = entities.TurnPhase.CONSTRUCTION


def fund_path_purchase(
    game: entities.ActiveGame, nickname: player.Nickname, *, count: int = 1
) -> None:
    services.grant_resources(
        game,
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
    services.grant_resources(
        game,
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
