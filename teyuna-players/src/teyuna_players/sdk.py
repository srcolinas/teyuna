"""HTTP client for the Teyuna game API.

Mirrors ``backend`` ``/games`` routes without importing that package.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
import httpx_sse

from . import entities

_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0, read=None),
)


def _raise_for_status(response: httpx.Response) -> None:
    """Like ``Response.raise_for_status`` but include API ``detail`` in the message."""
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail: str
        try:
            body = response.json()
            raw = body.get("detail", body) if isinstance(body, dict) else body
            detail = raw if isinstance(raw, str) else json.dumps(raw)
        except Exception:
            detail = response.text or str(exc)
        raise httpx.HTTPStatusError(
            f"{exc.response.status_code} {exc.response.reason_phrase} "
            f"for {exc.request.url}: {detail}",
            request=exc.request,
            response=exc.response,
        ) from None


class GameClient:
    """Async client for the Teyuna ``/games`` HTTP API."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def create_game(self, num_players: int) -> entities.Game:
        payload = entities.CreateGameRequest(num_players=num_players).model_dump(
            mode="json", exclude_none=True
        )
        response = await _http_client.post(f"{self._base_url}/games", json=payload)
        _raise_for_status(response)
        return entities.Game.model_validate(response.json())

    async def join_game(
        self, game_id: uuid.UUID, nickname: str
    ) -> AuthenticatedPlayerClient:
        response = await _http_client.post(
            f"{self._base_url}/games/{game_id}/players",
            json={"nickname": nickname},
        )
        _raise_for_status(response)
        token = response.cookies.get("session-token")
        if token is None:
            raise RuntimeError("join response did not include a session-token cookie")
        return AuthenticatedPlayerClient(self._base_url, token=token, game_id=game_id)

    async def get_game(self, game_id: uuid.UUID) -> entities.Game:
        response = await _http_client.get(f"{self._base_url}/games/{game_id}")
        _raise_for_status(response)
        return entities.Game.model_validate(response.json())

    async def get_map(self, game_id: uuid.UUID) -> tuple[entities.Hex, ...]:
        response = await _http_client.get(f"{self._base_url}/games/{game_id}/map")
        _raise_for_status(response)
        return tuple(entities.Hex.model_validate(item) for item in response.json())

    async def get_turn_order(self, game_id: uuid.UUID) -> tuple[str, ...]:
        response = await _http_client.get(
            f"{self._base_url}/games/{game_id}/turn-order"
        )
        _raise_for_status(response)
        return tuple(response.json())

    async def get_conquistator(self, game_id: uuid.UUID) -> entities.HexCoordinate:
        response = await _http_client.get(
            f"{self._base_url}/games/{game_id}/conquistator",
        )
        _raise_for_status(response)
        return entities.HexCoordinate.model_validate(response.json())

    async def list_players(self, game_id: uuid.UUID) -> list[entities.Player]:
        response = await _http_client.get(f"{self._base_url}/games/{game_id}/players")
        _raise_for_status(response)
        return [entities.Player.model_validate(item) for item in response.json()]

    async def get_player(self, game_id: uuid.UUID, nickname: str) -> entities.Player:
        response = await _http_client.get(
            f"{self._base_url}/games/{game_id}/players/{nickname}"
        )
        _raise_for_status(response)
        return entities.Player.model_validate(response.json())

    async def stream_events(self, game_id: uuid.UUID) -> AsyncIterator[dict[str, Any]]:
        async with httpx_sse.aconnect_sse(
            _http_client,
            "GET",
            f"{self._base_url}/games/{game_id}/events",
        ) as source:
            async for event in source.aiter_sse():
                if not event.data:
                    continue
                payload = json.loads(event.data)
                if isinstance(payload, dict):
                    yield payload
                else:
                    yield {"data": payload}


class AuthenticatedPlayerClient(GameClient):
    def __init__(self, base_url: str, token: str, game_id: uuid.UUID) -> None:
        super().__init__(base_url)
        self._cookies = {"session-token": token}
        self._game_id = game_id

    @property
    def game_id(self) -> uuid.UUID:
        return self._game_id

    async def advance_turn(self) -> tuple[entities.GamePhaseName, str]:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/turn-order",
            cookies=self._cookies,
        )
        _raise_for_status(response)
        phase, nickname = response.json()
        return entities.GamePhaseName(phase), nickname

    async def move_conquistator(
        self,
        location: entities.HexCoordinate,
        *,
        take_from: str | None = None,
    ) -> entities.HexCoordinate:
        payload: dict[str, Any] = {"location": location.model_dump(mode="json")}
        if take_from is not None:
            payload["take_from"] = take_from
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/conquistator",
            json=payload,
            cookies=self._cookies,
        )
        _raise_for_status(response)
        return entities.HexCoordinate.model_validate(response.json())

    async def play_wisdom_card(
        self, card: entities.WisdomCard
    ) -> entities.GamePhaseName:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards",
            cookies=self._cookies,
            json={"card": card.value},
        )
        _raise_for_status(response)
        return entities.GamePhaseName(response.json())

    async def buy_wisdom_card(self) -> entities.GamePhaseName:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/buy",
            cookies=self._cookies,
        )
        _raise_for_status(response)
        return entities.GamePhaseName(response.json())

    async def propose_trade(
        self,
        *,
        offer: dict[entities.ResourceCard, int],
        request: dict[entities.ResourceCard, int],
        to: set[str],
    ) -> None:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/trades",
            cookies=self._cookies,
            json={
                "offer": {k.value: v for k, v in offer.items()},
                "request": {k.value: v for k, v in request.items()},
                "to": list(to),
            },
        )
        _raise_for_status(response)

    async def accept_trade(self, proposal_id: uuid.UUID) -> entities.GamePhaseName:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/trades/{proposal_id}/accept",
            cookies=self._cookies,
        )
        _raise_for_status(response)
        return entities.GamePhaseName(response.json())

    async def trade_with_supply(
        self,
        *,
        offers: entities.ResourceCard,
        requests: entities.ResourceCard,
    ) -> entities.GamePhaseName:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/trades/supply",
            cookies=self._cookies,
            json={"offers": offers.value, "requests": requests.value},
        )
        _raise_for_status(response)
        return entities.GamePhaseName(response.json())

    async def play_mamo(
        self, resource: entities.ResourceCard
    ) -> dict[entities.ResourceCard, int]:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/mamo",
            cookies=self._cookies,
            json={"resource": resource.value},
        )
        _raise_for_status(response)
        return {
            entities.ResourceCard(key): value for key, value in response.json().items()
        }

    async def play_blessing(
        self,
        resources: tuple[entities.ResourceCard, entities.ResourceCard],
    ) -> dict[entities.ResourceCard, int]:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/blessing",
            cookies=self._cookies,
            json={"resources": [r.value for r in resources]},
        )
        _raise_for_status(response)
        return {
            entities.ResourceCard(key): value for key, value in response.json().items()
        }

    async def play_pathfinder(
        self, paths: list[entities.EdgeCoordinate]
    ) -> list[entities.PlayedStonePath]:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/pathfinder",
            cookies=self._cookies,
            json={"paths": [p.model_dump(mode="json") for p in paths]},
        )
        _raise_for_status(response)
        return [
            entities.PlayedStonePath.model_validate(item) for item in response.json()
        ]

    async def add_initial_placements(
        self,
        *,
        terrace: entities.VertexCoordinate,
        path: entities.EdgeCoordinate,
    ) -> tuple[entities.PlayedSettlement, entities.PlayedStonePath]:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/initial-placements",
            cookies=self._cookies,
            json={
                "terrace": terrace.model_dump(mode="json"),
                "path": path.model_dump(mode="json"),
            },
        )
        _raise_for_status(response)
        settlement, stone_path = response.json()
        return (
            entities.PlayedSettlement.model_validate(settlement),
            entities.PlayedStonePath.model_validate(stone_path),
        )

    async def build_settlement(
        self,
        *,
        item: entities.SettlementType,
        location: entities.VertexCoordinate,
    ) -> entities.PlayedSettlement:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/settlements",
            cookies=self._cookies,
            json={
                "item": item.value,
                "location": location.model_dump(mode="json"),
            },
        )
        _raise_for_status(response)
        return entities.PlayedSettlement.model_validate(response.json())

    async def build_path(
        self, location: entities.EdgeCoordinate
    ) -> entities.PlayedStonePath:
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/paths",
            cookies=self._cookies,
            json={"location": location.model_dump(mode="json")},
        )
        _raise_for_status(response)
        return entities.PlayedStonePath.model_validate(response.json())
