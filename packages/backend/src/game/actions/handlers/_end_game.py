import teyuna_core

from ... import entities


def handle_end_game(
    game: entities.Game, action: teyuna_core.PlayerAction
) -> teyuna_core.EndGameResult:
    previous_phase = game.phase
    game.phase = teyuna_core.GamePhaseName.END_GAME
    return teyuna_core.EndGameResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
    )


def handle_lobby_timeout(
    game: entities.Game, action: teyuna_core.PlayerAction
) -> teyuna_core.EndGameResult:
    previous_phase = game.phase
    game.phase = teyuna_core.GamePhaseName.END_GAME
    return teyuna_core.EndGameResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
    )
