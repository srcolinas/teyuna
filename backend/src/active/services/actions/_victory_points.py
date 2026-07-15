from .... import player
from ... import entities

_WIN_THRESHOLD: int = 10


def victory_points(game: entities.ActiveGame, by: player.Nickname, /) -> int:
    player_state = game.players[by]
    terraces = sum(
        1
        for settlement in player_state.settlements.values()
        if settlement is entities.SettlementType.TERRACE
    )
    great_terraces = sum(
        1
        for settlement in player_state.settlements.values()
        if settlement is entities.SettlementType.GREAT_TERRACE
    )
    points = terraces + 2 * great_terraces
    if game.longest_road[0] == by:
        points += 2
    if game.biggest_army[0] == by:
        points += 2
    points += player_state.played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS]
    return points


def declare_winner_if_eligible(
    game: entities.ActiveGame, by: player.Nickname, /
) -> bool:
    if victory_points(game, by) >= _WIN_THRESHOLD:
        game.winner = by
        return True
    return False
