# Understanding the board

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


