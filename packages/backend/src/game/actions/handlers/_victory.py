import teyuna_core

from ... import player, entities

_WIN_THRESHOLD: int = 10


def phase_after_victory_check(
    game: entities.Game,
    by: player.Nickname,
    fallback: teyuna_core.GamePhaseName,
    /,
) -> teyuna_core.GamePhaseName:
    if entities.victory_points(game, by) >= _WIN_THRESHOLD:
        return teyuna_core.GamePhaseName.END_GAME
    return fallback
