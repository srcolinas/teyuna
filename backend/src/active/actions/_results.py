from ._registry import ActionExecutionResult, GamePhaseName


def ok(phase: GamePhaseName) -> ActionExecutionResult:
    return ActionExecutionResult(succeeded=True, phase=phase)


def fail(error: Exception) -> ActionExecutionResult:
    """Failure placeholder; ``ActionsRegistry.execute`` sets ``phase`` to the current phase."""
    return ActionExecutionResult(
        succeeded=False,
        phase=GamePhaseName.END_GAME,
        error=error,
    )
