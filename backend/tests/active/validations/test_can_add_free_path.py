from src.active import entities, validations


def test_returns_true_when_path_is_free_and_adjacent_to_owned_terrace() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    assert (
        validations.can_add_free_path_at(
            target=path,
            neighbor_terrace=terrace,
            free_edges={path},
            existing_settlements={terrace},
        )
        is True
    )


def test_returns_false_when_path_not_free() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    assert (
        validations.can_add_free_path_at(
            target=path,
            neighbor_terrace=terrace,
            free_edges=set(),
            existing_settlements={terrace},
        )
        is False
    )


def test_returns_false_when_path_not_adjacent_to_terrace() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    other = entities.canonical_vertex(1, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(other.q, other.r, other.d)))
    assert terrace not in entities.vertices_of_edge(path)

    assert (
        validations.can_add_free_path_at(
            target=path,
            neighbor_terrace=terrace,
            free_edges={path},
            existing_settlements={terrace},
        )
        is False
    )


def test_returns_false_when_neighbor_terrace_not_owned() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    assert (
        validations.can_add_free_path_at(
            target=path,
            neighbor_terrace=terrace,
            free_edges={path},
            existing_settlements=set(),
        )
        is False
    )


def test_accepts_settlements_collection_locations() -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    settlements = entities.SettlementsCollection()
    settlements[terrace] = entities.SettlementType.TERRACE

    assert (
        validations.can_add_free_path_at(
            target=path,
            neighbor_terrace=terrace,
            free_edges={path},
            existing_settlements=settlements.locations(),
        )
        is True
    )
