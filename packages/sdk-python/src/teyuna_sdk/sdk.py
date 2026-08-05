"""HTTP client for the Teyuna game API.

Mirrors ``backend`` ``/games`` routes without importing that package.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Self

import httpx2
import pydantic

import teyuna_core

_http_client = httpx2.AsyncClient(
    timeout=httpx2.Timeout(30.0, read=None),
)


_action_result_adapter: pydantic.TypeAdapter[teyuna_core.AnyActionExecutionResult] = (
    pydantic.TypeAdapter(teyuna_core.AnyActionExecutionResult)
)
_game_event_adapter: pydantic.TypeAdapter[teyuna_core.AnyGameEvent] = (
    pydantic.TypeAdapter(teyuna_core.AnyGameEvent)
)


def _raise_for_status(response: httpx2.Response) -> None:
    """Like ``Response.raise_for_status`` but include API ``detail`` in the message."""
    try:
        response.raise_for_status()
    except httpx2.HTTPStatusError as exc:
        detail: str
        try:
            body = response.json()
            raw = body.get("detail", body) if isinstance(body, dict) else body
            detail = raw if isinstance(raw, str) else json.dumps(raw)
        except Exception:
            detail = response.text or str(exc)
        raise httpx2.HTTPStatusError(
            f"{exc.response.status_code} {exc.response.reason_phrase} "
            f"for {exc.request.url}: {detail}",
            request=exc.request,
            response=exc.response,
        ) from None


class GameClient:
    """Async client for the Teyuna ``/games`` HTTP API, bound to one game."""

    def __init__(self, base_url: str, game_id: uuid.UUID) -> None:
        self._base_url = base_url.rstrip("/")
        self._game_id = game_id
        self._token: str | None = None

    @property
    def game_id(self) -> uuid.UUID:
        """UUID of the game this client is bound to."""
        return self._game_id

    @property
    def token(self) -> str | None:
        """Session token for this client, or ``None`` if not authenticated."""
        return self._token

    @property
    def _headers(self) -> dict[str, str]:
        if self._token is None:
            raise RuntimeError(
                "GameClient is not authenticated; call authenticate() first"
            )
        return {"Authorization": f"Bearer {self._token}"}

    @classmethod
    async def create_game(cls, base_url: str, num_players: int) -> Self:
        """Create a new lobby game and return an unauthenticated client for it."""
        payload = teyuna_core.CreateGameRequest(num_players=num_players).model_dump(
            mode="json", exclude_none=True
        )
        url = base_url.rstrip("/")
        response = await _http_client.post(f"{url}/games", json=payload)
        _raise_for_status(response)
        game = teyuna_core.Game.model_validate(response.json())
        return cls(url, game.id)

    async def authenticate(self, nickname: str) -> Self:
        """Join the lobby as ``nickname``, store the session token, and return self."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/players",
            json={"nickname": nickname},
        )
        _raise_for_status(response)
        body = teyuna_core.JoinGameResponse.model_validate(response.json())
        self._token = body.token
        return self

    async def get_game(self) -> teyuna_core.Game:
        """Fetch the full public game state."""
        response = await _http_client.get(f"{self._base_url}/games/{self._game_id}")
        _raise_for_status(response)
        return teyuna_core.Game.model_validate(response.json())

    async def get_map(self) -> tuple[teyuna_core.Hex, ...]:
        """Fetch the board hex tiles for a game."""
        response = await _http_client.get(f"{self._base_url}/games/{self._game_id}/map")
        _raise_for_status(response)
        return tuple(teyuna_core.Hex.model_validate(item) for item in response.json())

    async def get_turn_order(self) -> tuple[str, ...]:
        """Fetch nicknames in turn order, starting with the active player."""
        response = await _http_client.get(
            f"{self._base_url}/games/{self._game_id}/turn-order"
        )
        _raise_for_status(response)
        return tuple(response.json())

    async def get_conquistator(self) -> teyuna_core.HexLocation:
        """Fetch the current Conquistador hex location."""
        response = await _http_client.get(
            f"{self._base_url}/games/{self._game_id}/conquistator",
        )
        _raise_for_status(response)
        return teyuna_core.HexLocation.model_validate(response.json())

    async def list_players(self) -> list[teyuna_core.Player]:
        """List all players' public info for a game."""
        response = await _http_client.get(
            f"{self._base_url}/games/{self._game_id}/players"
        )
        _raise_for_status(response)
        return [teyuna_core.Player.model_validate(item) for item in response.json()]

    async def get_player(self, nickname: str) -> teyuna_core.Player:
        """Fetch one player's public info by nickname."""
        response = await _http_client.get(
            f"{self._base_url}/games/{self._game_id}/players/{nickname}"
        )
        _raise_for_status(response)
        return teyuna_core.Player.model_validate(response.json())

    async def stream_events(self) -> AsyncIterator[teyuna_core.AnyGameEvent]:
        """Yield SSE game events as typed ``AnyGameEvent`` values."""
        async with _http_client.sse(
            f"{self._base_url}/games/{self._game_id}/events",
        ) as source:
            async for event in source:
                if not event.data:
                    continue
                yield _game_event_adapter.validate_json(event.data)

    async def get_hand(self) -> teyuna_core.PlayerHand:
        """Fetch this player's private resources and wisdom cards."""
        response = await _http_client.get(
            f"{self._base_url}/games/{self._game_id}/hand",
            headers=self._headers,
        )
        _raise_for_status(response)
        return teyuna_core.PlayerHand.model_validate(response.json())

    async def submit_action(
        self, action: teyuna_core.AnyPlayerAction
    ) -> teyuna_core.AnyActionExecutionResult:
        """Submit a clean player action; the server binds the actor from the session."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/actions",
            headers=self._headers,
            json=action.model_dump(mode="json"),
        )
        _raise_for_status(response)
        return _action_result_adapter.validate_python(response.json())

    async def send_message(self, text: str) -> None:
        """Send a chat message broadcast to all observers via SSE."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/messages",
            headers=self._headers,
            json={"text": text},
        )
        _raise_for_status(response)
