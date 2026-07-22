import teyuna_shared

from ... import player
from ... import entities

_WIN_THRESHOLD: int = 10


def victory_points(game: entities.Game, by: player.Nickname, /) -> int:
    player_state = game.players[by]
    settlements = player_state.settlements
    points = settlements.count(
        teyuna_shared.SettlementType.TERRACE
    ) + 2 * settlements.count(teyuna_shared.SettlementType.GREAT_TERRACE)
    if game.longest_road[0] == by:
        points += 2
    if game.biggest_army[0] == by:
        points += 2
    points += player_state.played_cards[teyuna_shared.WisdomCard.LEGACY_OF_THE_ELDERS]
    return points


def phase_after_victory_check(
    game: entities.Game,
    by: player.Nickname,
    fallback: teyuna_shared.GamePhaseName,
    /,
) -> teyuna_shared.GamePhaseName:
    if victory_points(game, by) >= _WIN_THRESHOLD:
        return teyuna_shared.GamePhaseName.END_GAME
    return fallback
