# How to play

The game is meant to be played through the its REST API. This document complements the API, which can be studied from `/openapi.json` and `/docs`. 

## Joining a game

Once a game is created, players wait for the expected number of players to join before they can take any action. To join a game, you send a `POST` request to `/games/{id}/players` with a nickname of choice in your payload (e.g `{"nickname": "srcolinas"}`); you will be given an object representing the state of the game and a token that you must use to identify yourself with the backend when performing an action or retrieving your hand. 

## Game state

There is a public game state that you can retrieve with a `GET` request to `/games/{id}` and it will tell you, among other things, where are the buildins already played and which vertices, the turn oder, the current phase of the game, where are some harbours, etc., you can check all returned fields from `/openapi.json` and `/docs`. 

The object will also tell you information about players, but some of that information is hiden and it is only available to them, like the specific resources they hold and the wisdom cards they have not played. Any player can keep track of their own hand based on production upon dice roll and the wisdom cards they buy, but a player can also retrieve their own hand if they make a `GET` request to `/games/{id}/hand` using the token given upon authentication.

## Map

The map is a pointy-top hexagonal grid. Each hexagon tile is located with axial coordinates `(q, r)`. The central hexagon is at `(0, 0)` from there q  `q` increases and decreases along the bottom-left to top-right diagonal; likewise `r` increases and decreases along the vertical axis. The board has 19 hexes — every `(q, r)` with both in `[-2, 2]` except the following values that never happen `(-2,-2)`, `(-2,-1)`, `(-1,-2)`, `(1,2)`, `(2,1)`, and `(2,2)`. 

Here are some examples to help you visualize the coordinate system. Imagine you are at `(0, 0)` in the center, then:
* If you go along the q diagonal you find the `(1, -1)` and the `(-1, 1)` hexagons, each at opposite sites with respect to the hexagon at `(0,0)`.
* If you move along the horizontal (`r=0`), you find the `(-1, 0)` and the `(1, 0)` hexagons, also opposite to each other.
* If you move above the other diagonal (`q=0`), you find the `(0, -1)` and the `(0, 1)` hexagons, also opposite to each other. 

Something useful to notice is that if you move along a horizontal (not only the bigger one, but each horizontal movement), the hexagons always have the same value for `r`, only the values of `q` change. If you move along the top-left to bottom-tight diagonal (or a parallel), the hexagons always have the same value of `q`, only the value of `r` changes.

If you need more information, go through the following readings:
* https://www.redblobgames.com/grids/hexagons/#coordinates-axial
* https://srcolinas.substack.com/i/201200979/the-api 

To locate vertices (for terraces and great terraces) and edges (for paths) in the map, we add a direction `d` on a neighboring hex: `( "q", "r", "d" )`. On a given hex, `d` runs clockwise from 0 to 5. For a vertex, `d = 0` is the top corner. For an edge, `d = 0` is the upper-right side (between vertices `0` and `1`). Notice that a single edge or vertex can be described in a few forms. For example, the `(0, 0, 0)` vertex is the same as the `(0, -1, 2)` and the `(1, -1, 4)`; likewise, the edge `(0, 0, 1)` is the same as the `(1, 0, 4)`. The server internaly has a canonical representation and uses the notation that minimizes `q`, `r` and `d` (in that order), so the vertex at `(0,0,0)` is actually referenced as `(0, -1, 2)` and the edge at `(0, 0, 1)` is referenced like that. When calling the API and referencing a vertex or an edge, you don't need to pass the canonical representation, but you do need to understand it when you interpret outputs from the backend.   


## Phase → action map

Exact `Game.phase` strings:


| Phase                                                      | Who acts                                   | Legal `kind` values                                                                                                                                 |
| ---------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lobby`                                                    | —                                          | No player actions (join only)                                                                                                                       |
| `first placement`                                          | Active (`turn_order[0]`)                   | `free_placement`, `advance`                                                                                                                         |
| `second placement`                                         | Active                                     | `free_placement`, `advance`                                                                                                                         |
| `dice roll`                                                | Active; others may propose trade to active | `advance` (roll), `play_wisdom_card`, `propose_trade`                                                                                               |
| `discard resources`                                        | Players listed in `to_discard_resources`   | `discard_resources` only                                                                                                                            |
| `move conquistator`                                        | Active                                     | `move_conquistator`, `advance`                                                                                                                      |
| `dice play warrior` / `trade and build play warrior`       | Active                                     | `move_conquistator`, `advance`                                                                                                                      |
| `dice play mamo` / `trade and build play mamo`             | Active                                     | `play_mamo`, `advance`                                                                                                                              |
| `dice play blessed` / `trade and build play blessed`       | Active                                     | `play_blessed`, `advance`                                                                                                                           |
| `dice play pathfinder` / `trade and build play pathfinder` | Active                                     | `play_pathfinder`, `advance`                                                                                                                        |
| `trade and build`                                          | Active; accept trade by target             | `build_settlement`, `build_path`, `buy_wisdom_card`, `propose_trade`, `accept_trade`, `trade_with_supply`, `play_wisdom_card`, `advance` (end turn) |
| `end game`                                                 | —                                          | Stop                                                                                                                                                |


Additionally, you can send messages to other player with a `POST` request to `/games/{id}/messages`. All effects of acctions taken by any player, as well as other sever events can be read from the stream at `/games/{id}/events`.



### Sample payloads for actions


#### advance

```json
{ "kind": "advance" }
```


#### free_placement

```json
{
  "kind": "free_placement",
  "terrace": { "q": 0, "r": -1, "d": 2 },
  "path": { "q": 0, "r": -1, "d": 2 }
}
```

Omit `terrace` / `path` (or use `advance`) for a server-chosen legal placement.

#### discard_resources

```json
{
  "kind": "discard_resources",
  "count": { "wood": 2, "gold": 2 }
}
```

Totals in `count` must equal your entry in `to_discard_resources`.

#### move_conquistator

```json
{
  "kind": "move_conquistator",
  "q": 1,
  "r": -1,
  "from_player": "bob"
}
```

`from_player` is optional (steal target adjacent to the destination hex).

#### play_wisdom_card

```json
{ "kind": "play_wisdom_card", "card": "warrior" }
```

Card strings: `warrior`, `blessing of aluna`, `wisdom of mamo`, `pathfinder`, `legacy of the elders`.

#### play_mamo / play_blessed / play_pathfinder

```json
{ "kind": "play_mamo", "resource": "wood" }
```

```json
{ "kind": "play_blessed", "resources": ["gold", "maize"] }
```

```json
{
  "kind": "play_pathfinder",
  "paths": [
    { "q": 0, "r": 0, "d": 1 },
    { "q": 0, "r": 0, "d": 2 }
  ]
}
```



#### build_settlement / build_path / buy_wisdom_card

Building types: `terrace`, `great terrace`. Paths use edges.

```json
{
  "kind": "build_settlement",
  "item": "terrace",
  "coordinate": { "q": 0, "r": 0, "d": 0 }
}
```

```json
{
  "kind": "build_path",
  "coordinate": { "q": 0, "r": 0, "d": 1 }
}
```

```json
{ "kind": "buy_wisdom_card" }
```



#### Trades

```json
{
  "kind": "propose_trade",
  "offer": { "gold": 1 },
  "request": { "stone": 1 },
  "to": ["bob"]
}
```

```json
{ "kind": "accept_trade", "id": "00000000-0000-0000-0000-000000000001" }
```

```json
{
  "kind": "trade_with_supply",
  "offers": "gold",
  "requests": "stone"
}
```
