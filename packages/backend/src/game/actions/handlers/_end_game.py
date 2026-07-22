import teyuna_shared

from ... import entities


def handle_end_game(
    game: entities.Game, action: teyuna_shared.PlayerAction
) -> teyuna_shared.EndGameResult:
    previous_phase = game.phase
    game.phase = teyuna_shared.GamePhaseName.END_GAME
    return teyuna_shared.EndGameResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
    )


def handle_lobby_timeout(
    game: entities.Game, action: teyuna_shared.PlayerAction
) -> teyuna_shared.EndGameResult:
    previous_phase = game.phase
    game.phase = teyuna_shared.GamePhaseName.END_GAME
    return teyuna_shared.EndGameResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
    )
