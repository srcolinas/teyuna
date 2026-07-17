from src.active import entities, validations


def test_returns_true_when_free_and_adjacent_to_owned_path() -> None:
    target = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(target.q, target.r, target.d)))

    assert (
        validations.can_build_terrace_at(
            free_verticies={target},
            restricted_verticies=set(),
            existing_paths={path},
            target=target,
        )
        is True
    )


def test_returns_false_when_no_adjacent_owned_path() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        validations.can_build_terrace_at(
            free_verticies={target},
            restricted_verticies=set(),
            existing_paths=set(),
            target=target,
        )
        is False
    )


def test_returns_false_when_target_is_restricted() -> None:
    target = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(target.q, target.r, target.d)))

    assert (
        validations.can_build_terrace_at(
            free_verticies={target},
            restricted_verticies={target},
            existing_paths={path},
            target=target,
        )
        is False
    )


def test_returns_false_when_target_not_free() -> None:
    target = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(target.q, target.r, target.d)))

    assert (
        validations.can_build_terrace_at(
            free_verticies=set(),
            restricted_verticies=set(),
            existing_paths={path},
            target=target,
        )
        is False
    )
