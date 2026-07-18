from .... import player
from ... import entities
from .. import _registry

_WIN_THRESHOLD: int = 10


def victory_points(game: entities.ActiveGame, by: player.Nickname, /) -> int:
    player_state = game.players[by]
    settlements = player_state.settlements
    points = settlements.count(entities.SettlementType.TERRACE) + 2 * settlements.count(
        entities.SettlementType.GREAT_TERRACE
    )
    if game.longest_road[0] == by:
        points += 2
    if game.biggest_army[0] == by:
        points += 2
    points += player_state.played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS]
    return points


def phase_after_victory_check(
    game: entities.ActiveGame,
    by: player.Nickname,
    fallback: _registry.GamePhaseName,
    /,
) -> _registry.GamePhaseName:
    if victory_points(game, by) >= _WIN_THRESHOLD:
        return _registry.GamePhaseName.END_GAME
    return fallback
