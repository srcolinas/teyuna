import contextlib
import datetime
import uuid
from typing import cast

from src import active, player, proposed


def create_game_and_add_players(
    *,
    active_repository: active.InMemoryActiveGameRepository,
    max_players: int = 3,
    players_to_add: int = 3,
    nicknames: list[player.Nickname] | None = None,
) -> uuid.UUID:
    auth = player.PlayerAuthenticationService()
    proposed_repository = proposed.InMemoryProposedGameRepository()
    manager = active.GameManager(active_repository)

    proposed_game_id = proposed_repository.add(
        num_players=max_players,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id

    if nicknames is None:
        nicknames = [f"srcolinas-{i}" for i in range(players_to_add)]

    for i in range(players_to_add - 1):
        proposed.add_player(
            game_id=proposed_game_id,
            nickname=nicknames[i],
            repository=proposed_repository,
            manager=manager,
            auth=auth,
        )

    result, _ = proposed.add_player(
        game_id=proposed_game_id,
        nickname=nicknames[players_to_add - 1],
        repository=proposed_repository,
        manager=manager,
        auth=auth,
    )
    result = cast(proposed.PlayerAddedResult, result)
    game = cast(uuid.UUID, result.game)
    return game


@contextlib.contextmanager
def assert_not_raises(ExpectedException):
    try:
        yield

    except ExpectedException:
        raise AssertionError(
            "Did raise exception {0} when it should not!".format(
                repr(ExpectedException)
            )
        )

    except Exception as e:
        raise AssertionError("An unexpected exception {0} raised.".format(repr(e)))
