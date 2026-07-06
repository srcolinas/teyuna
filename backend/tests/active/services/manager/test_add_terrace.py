import itertools

import pytest

from src import active
from src.active import entities


def test_terrace_can_be_added_by_player_in_turn(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    manager = active.GameManager(repository)
    id = manager.start(players=["srcolinas-1", "srcolinas-2", "srcolinas-3"])
    game = repository.retrieve(id)
    nickname = game.turn_order[0]
    settlement = manager.add_terrace(id, nickname, q=0, r=0, direction=0)
    assert settlement == entities.Settlement(
        location=entities.VertexCoordinate(
            hex_coord=entities.HexCoordinate(q=0, r=0), direction=0
        ),
        type=entities.SettlementType.TERRACE,
    )


def test_terrace_is_added_to_game_object(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    manager = active.GameManager(repository)
    id = manager.start(players=["srcolinas-1", "srcolinas-2", "srcolinas-3"])
    game = repository.retrieve(id)
    nickname = game.turn_order[0]
    settlement = manager.add_terrace(id, nickname, q=0, r=0, direction=0)
    assert game.players[nickname].settlements[0] == settlement


@pytest.mark.parametrize(
    "valid,invalid",
    list(
        itertools.product(
            [(0, 0, 0)],
            [
                (0, 0, 0),
                (0, 0, 1),
                (0, 0, 5),
                (1, -1, 3),
                (1, -1, 4),
                (1, -1, 5),
                (0, -1, 1),
                (0, -1, 2),
                (0, -1, 3),
            ],
        )
    ),
)
def test_terrace_cannot_be_added_to_restricted_location(
    valid: tuple[int, int, int],
    invalid: tuple[int, int, int],
    repository: active.InMemoryActiveGameRepository,
) -> None:
    manager = active.GameManager(repository)
    id = manager.start(players=["srcolinas-1", "srcolinas-2", "srcolinas-3"])
    game = repository.retrieve(id)
    nickname = game.turn_order[0]
    q, r, d = valid
    manager.add_terrace(id, nickname, q=q, r=r, direction=d)
    nickname = game.turn_order[0]
    with pytest.raises(active.InvalidSettlementLocation):
        q, r, d = invalid
        manager.add_terrace(id, nickname, q=q, r=r, direction=d)
