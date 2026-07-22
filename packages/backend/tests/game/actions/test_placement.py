from src.game import entities
from src.game.actions.handlers import _placement


def test_free_path_returns_true_when_adjacent_to_owned_settlement() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    assert (
        _placement.can_add_free_path_at(
            target=path,
            free_edges={path},
            existing_settlements={terrace},
            existing_paths=set(),
            free_vertices=set(),
        )
        is True
    )


def test_free_path_returns_false_when_path_not_free() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    assert (
        _placement.can_add_free_path_at(
            target=path,
            free_edges=set(),
            existing_settlements={terrace},
            existing_paths=set(),
            free_vertices=set(),
        )
        is False
    )


def test_free_path_returns_false_when_disconnected() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    other = entities.canonical_vertex(1, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(other.q, other.r, other.d)))
    assert terrace not in entities.vertices_of_edge(path)

    assert (
        _placement.can_add_free_path_at(
            target=path,
            free_edges={path},
            existing_settlements={terrace},
            existing_paths=set(),
            free_vertices=set(),
        )
        is False
    )


def test_free_path_returns_true_when_adjacent_to_free_vertex_with_owned_path() -> None:
    owned_path = entities.canonical_edge(0, 0, 0)
    v0, v1 = entities.vertices_of_edge(owned_path)
    adjacent = next(
        e
        for e in entities.edges_adjacent_to_vertex(v1.q, v1.r, v1.d)
        if e != owned_path
    )

    assert (
        _placement.can_add_free_path_at(
            target=adjacent,
            free_edges={adjacent},
            existing_settlements=set(),
            existing_paths={owned_path},
            free_vertices={v1},
        )
        is True
    )


def test_free_path_returns_false_when_neighbor_settlement_not_owned() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    assert (
        _placement.can_add_free_path_at(
            target=path,
            free_edges={path},
            existing_settlements=set(),
            existing_paths=set(),
            free_vertices=set(),
        )
        is False
    )


def test_free_path_returns_true_when_adjacent_to_new_settlement() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    assert (
        _placement.can_add_free_path_at(
            target=path,
            free_edges={path},
            existing_settlements=set(),
            existing_paths=set(),
            free_vertices=set(),
            new_settlement=terrace,
        )
        is True
    )


def test_free_path_accepts_settlements_collection_locations() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    settlements = entities.SettlementsCollection()
    settlements[terrace] = entities.SettlementType.TERRACE

    assert list(settlements.values()) == [entities.SettlementType.TERRACE]
    assert (
        _placement.can_add_free_path_at(
            target=path,
            free_edges={path},
            existing_settlements=settlements.locations(),
            existing_paths=set(),
            free_vertices=set(),
        )
        is True
    )


def test_free_terrace_returns_true_when_target_is_free() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        _placement.can_add_free_terrace_at(
            free_verticies={target},
            restricted_verticies=set(),
            target=target,
        )
        is True
    )


def test_free_terrace_returns_false_when_target_not_free() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        _placement.can_add_free_terrace_at(
            free_verticies=set(),
            restricted_verticies=set(),
            target=target,
        )
        is False
    )


def test_free_terrace_returns_false_when_target_is_restricted() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        _placement.can_add_free_terrace_at(
            free_verticies={target},
            restricted_verticies={target},
            target=target,
        )
        is False
    )


def test_build_terrace_returns_true_when_free_and_adjacent_to_owned_path() -> None:
    target = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(target.q, target.r, target.d)))

    assert (
        _placement.can_build_terrace_at(
            free_verticies={target},
            restricted_verticies=set(),
            existing_paths={path},
            target=target,
        )
        is True
    )


def test_build_terrace_returns_false_when_no_adjacent_owned_path() -> None:
    target = entities.canonical_vertex(0, 0, 0)

    assert (
        _placement.can_build_terrace_at(
            free_verticies={target},
            restricted_verticies=set(),
            existing_paths=set(),
            target=target,
        )
        is False
    )


def test_build_terrace_returns_false_when_target_is_restricted() -> None:
    target = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(target.q, target.r, target.d)))

    assert (
        _placement.can_build_terrace_at(
            free_verticies={target},
            restricted_verticies={target},
            existing_paths={path},
            target=target,
        )
        is False
    )


def test_build_terrace_returns_false_when_target_not_free() -> None:
    target = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(target.q, target.r, target.d)))

    assert (
        _placement.can_build_terrace_at(
            free_verticies=set(),
            restricted_verticies=set(),
            existing_paths={path},
            target=target,
        )
        is False
    )
