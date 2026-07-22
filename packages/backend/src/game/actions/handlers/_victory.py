import teyuna_shared

from ... import player, entities

_WIN_THRESHOLD: int = 10


def phase_after_victory_check(
    game: entities.Game,
    by: player.Nickname,
    fallback: teyuna_shared.GamePhaseName,
    /,
) -> teyuna_shared.GamePhaseName:
    if entities.victory_points(game, by) >= _WIN_THRESHOLD:
        return teyuna_shared.GamePhaseName.END_GAME
    return fallback
