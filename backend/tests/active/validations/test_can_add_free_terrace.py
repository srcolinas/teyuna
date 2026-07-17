from src.active import entities, validations


def test_returns_true_when_target_is_free() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        validations.can_add_free_terrace_at(
            free_verticies={target},
            restricted_verticies=set(),
            target=target,
        )
        is True
    )


def test_returns_false_when_target_not_free() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        validations.can_add_free_terrace_at(
            free_verticies=set(),
            restricted_verticies=set(),
            target=target,
        )
        is False
    )


def test_returns_false_when_target_is_restricted() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        validations.can_add_free_terrace_at(
            free_verticies={target},
            restricted_verticies={target},
            target=target,
        )
        is False
    )
