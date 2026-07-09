import uuid
from typing import Annotated

import fastapi
import pydantic
from fastapi import status

from .. import active, player
from . import dependencies, entities, ports, repository
from .services import _add_player, _create

router = fastapi.APIRouter(prefix="/proposed-games", tags=["games"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_game(
    payload: ports.CreateGameRequest,
    repository_: Annotated[
        _create.CreateGameRepository, fastapi.Depends(dependencies.get_repository)
    ],
) -> entities.ProposedGame:
    return _create.create_game(params=payload, repository=repository_)


class JoinGameRequest(pydantic.BaseModel):
    nickname: player.Nickname


@router.post("/{game_id}/players")
def join_game(
    response: fastapi.Response,
    game_id: uuid.UUID,
    payload: JoinGameRequest,
    repository_: Annotated[
        _add_player.AddPlayerGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    game_repository: Annotated[
        active.repository.InMemoryActiveGameRepository,
        fastapi.Depends(active.dependencies.get_repository),
    ],
    auth: Annotated[
        player.PlayerAuthenticationService, fastapi.Depends(player.service)
    ],
) -> _add_player.PlayerAddedResult:
    try:
        result, token = _add_player.add_player(
            game_id=game_id,
            nickname=payload.nickname,
            repository=repository_,
            game_repository=game_repository,
            auth=auth,
        )
    except _add_player.GameAlreadyFullError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game already full"
        )
    except _add_player.GameExpiredError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game expired"
        )
    except repository.ProposedGameDoesNotExistError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game doesn't exist"
        )
    response.set_cookie(key="session-token", value=token, httponly=True)
    return result
