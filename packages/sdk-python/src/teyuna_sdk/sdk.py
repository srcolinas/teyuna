"""HTTP client for the Teyuna game API.

Mirrors ``backend`` ``/games`` routes without importing that package.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx2

import teyuna_shared

_http_client = httpx2.AsyncClient(
    timeout=httpx2.Timeout(30.0, read=None),
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
    """Async client for the Teyuna ``/games`` HTTP API."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def create_game(self, num_players: int) -> teyuna_shared.Game:
        """Create a new lobby game with ``num_players`` seats (3–4)."""
        payload = teyuna_shared.CreateGameRequest(num_players=num_players).model_dump(
            mode="json", exclude_none=True
        )
        response = await _http_client.post(f"{self._base_url}/games", json=payload)
        _raise_for_status(response)
        return teyuna_shared.Game.model_validate(response.json())

    async def join_game(
        self, game_id: uuid.UUID, nickname: str
    ) -> AuthenticatedPlayerClient:
        """Join a lobby game and return an authenticated player client."""
        response = await _http_client.post(
            f"{self._base_url}/games/{game_id}/players",
            json={"nickname": nickname},
        )
        _raise_for_status(response)
        body = teyuna_shared.JoinGameResponse.model_validate(response.json())
        return AuthenticatedPlayerClient(
            self._base_url, token=body.token, game_id=game_id
        )

    async def get_game(self, game_id: uuid.UUID) -> teyuna_shared.Game:
        """Fetch the full public game state."""
        response = await _http_client.get(f"{self._base_url}/games/{game_id}")
        _raise_for_status(response)
        return teyuna_shared.Game.model_validate(response.json())

    async def get_map(self, game_id: uuid.UUID) -> tuple[teyuna_shared.Hex, ...]:
        """Fetch the board hex tiles for a game."""
        response = await _http_client.get(f"{self._base_url}/games/{game_id}/map")
        _raise_for_status(response)
        return tuple(teyuna_shared.Hex.model_validate(item) for item in response.json())

    async def get_turn_order(self, game_id: uuid.UUID) -> tuple[str, ...]:
        """Fetch nicknames in turn order, starting with the active player."""
        response = await _http_client.get(
            f"{self._base_url}/games/{game_id}/turn-order"
        )
        _raise_for_status(response)
        return tuple(response.json())

    async def get_conquistator(self, game_id: uuid.UUID) -> teyuna_shared.HexCoordinate:
        """Fetch the current Conquistador hex location."""
        response = await _http_client.get(
            f"{self._base_url}/games/{game_id}/conquistator",
        )
        _raise_for_status(response)
        return teyuna_shared.HexCoordinate.model_validate(response.json())

    async def list_players(self, game_id: uuid.UUID) -> list[teyuna_shared.Player]:
        """List all players' public info for a game."""
        response = await _http_client.get(f"{self._base_url}/games/{game_id}/players")
        _raise_for_status(response)
        return [teyuna_shared.Player.model_validate(item) for item in response.json()]

    async def get_player(
        self, game_id: uuid.UUID, nickname: str
    ) -> teyuna_shared.Player:
        """Fetch one player's public info by nickname."""
        response = await _http_client.get(
            f"{self._base_url}/games/{game_id}/players/{nickname}"
        )
        _raise_for_status(response)
        return teyuna_shared.Player.model_validate(response.json())

    async def stream_events(self, game_id: uuid.UUID) -> AsyncIterator[dict[str, Any]]:
        """Yield SSE game-action events as parsed JSON dicts."""
        async with _http_client.sse(
            f"{self._base_url}/games/{game_id}/events",
        ) as source:
            async for event in source:
                if not event.data:
                    continue
                payload = json.loads(event.data)
                if isinstance(payload, dict):
                    yield payload
                else:
                    yield {"data": payload}


class AuthenticatedPlayerClient(GameClient):
    """Player client bound to a game with an Authorization Bearer token."""

    def __init__(self, base_url: str, token: str, game_id: uuid.UUID) -> None:
        super().__init__(base_url)
        self._token = token
        self._headers = {"Authorization": f"Bearer {token}"}
        self._game_id = game_id

    @property
    def game_id(self) -> uuid.UUID:
        """UUID of the game this client is authenticated for."""
        return self._game_id

    @property
    def token(self) -> str:
        """Bearer token issued when this player joined the game."""
        return self._token

    async def get_hand(self) -> teyuna_shared.PlayerHand:
        """Fetch this player's private resources and wisdom cards."""
        response = await _http_client.get(
            f"{self._base_url}/games/{self._game_id}/hand",
            headers=self._headers,
        )
        _raise_for_status(response)
        return teyuna_shared.PlayerHand.model_validate(response.json())

    async def advance_turn(self) -> tuple[teyuna_shared.GamePhaseName, str]:
        """Roll dice (dice-roll phase) or end the turn (trade-and-build phase)."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/turn-order",
            headers=self._headers,
        )
        _raise_for_status(response)
        phase, nickname = response.json()
        return teyuna_shared.GamePhaseName(phase), nickname

    async def move_conquistator(
        self,
        location: teyuna_shared.HexCoordinate,
        *,
        take_from: str | None = None,
    ) -> teyuna_shared.HexCoordinate:
        """Move the Conquistador; optionally steal from ``take_from``."""
        payload: dict[str, Any] = {"location": location.model_dump(mode="json")}
        if take_from is not None:
            payload["take_from"] = take_from
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/conquistator",
            json=payload,
            headers=self._headers,
        )
        _raise_for_status(response)
        return teyuna_shared.HexCoordinate.model_validate(response.json())

    async def discard_resources(
        self, count: dict[teyuna_shared.ResourceCard, int]
    ) -> teyuna_shared.GamePhaseName:
        """Discard resources after a 7 is rolled (when required)."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/discard",
            headers=self._headers,
            json={"count": {k.value: v for k, v in count.items()}},
        )
        _raise_for_status(response)
        return teyuna_shared.GamePhaseName(response.json())

    async def play_wisdom_card(
        self, card: teyuna_shared.WisdomCard
    ) -> teyuna_shared.GamePhaseName:
        """Play a wisdom card from hand; may enter a resolution sub-phase."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards",
            headers=self._headers,
            json={"card": card.value},
        )
        _raise_for_status(response)
        return teyuna_shared.GamePhaseName(response.json())

    async def buy_wisdom_card(self) -> teyuna_shared.GamePhaseName:
        """Buy a wisdom card from the deck during trade-and-build."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/buy",
            headers=self._headers,
        )
        _raise_for_status(response)
        return teyuna_shared.GamePhaseName(response.json())

    async def propose_trade(
        self,
        *,
        offer: dict[teyuna_shared.ResourceCard, int],
        request: dict[teyuna_shared.ResourceCard, int],
        to: set[str],
    ) -> None:
        """Propose a player-to-player trade to the nicknames in ``to``."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/trades",
            headers=self._headers,
            json={
                "offer": {k.value: v for k, v in offer.items()},
                "request": {k.value: v for k, v in request.items()},
                "to": list(to),
            },
        )
        _raise_for_status(response)

    async def accept_trade(self, proposal_id: uuid.UUID) -> teyuna_shared.GamePhaseName:
        """Accept an open trade proposal by id."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/trades/{proposal_id}/accept",
            headers=self._headers,
        )
        _raise_for_status(response)
        return teyuna_shared.GamePhaseName(response.json())

    async def trade_with_supply(
        self,
        *,
        offers: teyuna_shared.ResourceCard,
        requests: teyuna_shared.ResourceCard,
    ) -> teyuna_shared.GamePhaseName:
        """Trade with the bank/supply at the applicable harbour rate."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/trades/supply",
            headers=self._headers,
            json={"offers": offers.value, "requests": requests.value},
        )
        _raise_for_status(response)
        return teyuna_shared.GamePhaseName(response.json())

    async def play_mamo(
        self, resource: teyuna_shared.ResourceCard
    ) -> dict[teyuna_shared.ResourceCard, int]:
        """Resolve Wisdom of the Mamo by naming a resource to monopolize."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/mamo",
            headers=self._headers,
            json={"resource": resource.value},
        )
        _raise_for_status(response)
        return {
            teyuna_shared.ResourceCard(key): value
            for key, value in response.json().items()
        }

    async def play_blessing(
        self,
        resources: tuple[teyuna_shared.ResourceCard, teyuna_shared.ResourceCard],
    ) -> dict[teyuna_shared.ResourceCard, int]:
        """Resolve Blessing of Aluna by choosing two resources to take."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/blessing",
            headers=self._headers,
            json={"resources": [r.value for r in resources]},
        )
        _raise_for_status(response)
        return {
            teyuna_shared.ResourceCard(key): value
            for key, value in response.json().items()
        }

    async def play_pathfinder(
        self, paths: list[teyuna_shared.EdgeCoordinate]
    ) -> list[teyuna_shared.PlayedStonePath]:
        """Resolve Pathfinder by placing one or two free stone paths."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/wisdom-cards/pathfinder",
            headers=self._headers,
            json={"paths": [p.model_dump(mode="json") for p in paths]},
        )
        _raise_for_status(response)
        return [
            teyuna_shared.PlayedStonePath.model_validate(item)
            for item in response.json()
        ]

    async def send_message(self, text: str) -> None:
        """Send a chat message broadcast to all observers via SSE."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/messages",
            headers=self._headers,
            json={"text": text},
        )
        _raise_for_status(response)

    async def add_initial_placements(
        self,
        *,
        terrace: teyuna_shared.VertexCoordinate | None = None,
        path: teyuna_shared.EdgeCoordinate | None = None,
    ) -> tuple[teyuna_shared.PlayedSettlement, teyuna_shared.PlayedStonePath]:
        """Place a free terrace and path in setup; omit both to skip/timeout."""
        body: dict[str, object] = {}
        if terrace is not None:
            body["terrace"] = terrace.model_dump(mode="json")
        if path is not None:
            body["path"] = path.model_dump(mode="json")
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/initial-placements",
            headers=self._headers,
            json=body,
        )
        _raise_for_status(response)
        settlement, stone_path = response.json()
        return (
            teyuna_shared.PlayedSettlement.model_validate(settlement),
            teyuna_shared.PlayedStonePath.model_validate(stone_path),
        )

    async def build_settlement(
        self,
        *,
        item: teyuna_shared.SettlementType,
        location: teyuna_shared.VertexCoordinate,
    ) -> teyuna_shared.PlayedSettlement:
        """Build a terrace or upgrade to a great terrace at ``location``."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/settlements",
            headers=self._headers,
            json={
                "item": item.value,
                "location": location.model_dump(mode="json"),
            },
        )
        _raise_for_status(response)
        return teyuna_shared.PlayedSettlement.model_validate(response.json())

    async def build_path(
        self, location: teyuna_shared.EdgeCoordinate
    ) -> teyuna_shared.PlayedStonePath:
        """Build a stone path at ``location`` during trade-and-build."""
        response = await _http_client.post(
            f"{self._base_url}/games/{self._game_id}/paths",
            headers=self._headers,
            json={"location": location.model_dump(mode="json")},
        )
        _raise_for_status(response)
        return teyuna_shared.PlayedStonePath.model_validate(response.json())
