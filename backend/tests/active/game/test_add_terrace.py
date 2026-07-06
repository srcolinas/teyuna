import itertools

import pytest

from src.active import entities


def test_terrace_can_be_added_by_player_in_turn() -> None:
    game = entities.ActiveGame.create_new(["srcolinas-1", "srcolinas-2", "srcolinas-3"])
    nickname = game.turn_order[0]
    settlement = game.add_terrace(nickname, q=0, r=0, direction=0)
    assert settlement == entities.Settlement(
        location=entities.VertexCoordinate(
            hex_coord=entities.HexCoordinate(q=0, r=0), direction=0
        ),
        type=entities.SettlementType.TERRACE,
    )


def test_terrace_is_added_to_game_object() -> None:
    game = entities.ActiveGame.create_new(["srcolinas-1", "srcolinas-2", "srcolinas-3"])
    nickname = game.turn_order[0]
    settlement = game.add_terrace(nickname, q=0, r=0, direction=0)
    assert game.players[nickname].settlements[settlement.location] == settlement.type


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
) -> None:
    game = entities.ActiveGame.create_new(["srcolinas-1", "srcolinas-2", "srcolinas-3"])
    nickname = game.turn_order[0]
    q, r, d = valid
    game.add_terrace(nickname, q=q, r=r, direction=d)
    nickname = game.turn_order[0]
    with pytest.raises(entities.InvalidSettlementLocation):
        q, r, d = invalid
        game.add_terrace(nickname, q=q, r=r, direction=d)


def test_terrace_cannot_be_added_by_player_not_in_turn() -> None:
    game = entities.ActiveGame.create_new(["srcolinas-1", "srcolinas-2", "srcolinas-3"])
    nickname = game.turn_order[1]
    with pytest.raises(entities.PlayerNotInTurn):
        game.add_terrace(nickname, q=0, r=0, direction=0)
