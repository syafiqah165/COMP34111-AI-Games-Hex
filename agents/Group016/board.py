"""Fast board representation for Group016's Hex agent.

The engine's Board stores Tile objects and has no undo, which is too slow for
an agent that tries many moves. HexBoard keeps its own copy of the position:

- cells: a flat list, one entry per cell, EMPTY (0), RED (1) or BLUE (2).
- A cell (x, y) is stored at index x * size + y, the same (x, y) as the
  engine's board.tiles[x][y] and Move(x, y).
- Red connects the top row (x == 0) to the bottom row (x == size - 1).
  Blue connects the left column (y == 0) to the right column (y == size - 1).

This module only answers questions about a position. It does not decide which
move to play; that belongs to the agent.
"""

from src.Board import Board
from src.Colour import Colour
from src.Tile import Tile

EMPTY, RED, BLUE = 0, 1, 2

# Neighbour tables are the same for every board of a given size, so they are
# built once and shared.
_NEIGHBOURS_CACHE: dict[int, list[tuple[int, ...]]] = {}


def colour_to_player(colour: Colour) -> int:
    """Engine Colour -> RED or BLUE."""
    return RED if colour == Colour.RED else BLUE


def opponent(player: int) -> int:
    """RED <-> BLUE."""
    return 3 - player


def _build_neighbours(size: int) -> list[tuple[int, ...]]:
    """For each cell index, the indices of its (up to 6) neighbours."""
    if size not in _NEIGHBOURS_CACHE:
        table = []
        for x in range(size):
            for y in range(size):
                nb = []
                for k in range(Tile.NEIGHBOUR_COUNT):
                    nx = x + Tile.I_DISPLACEMENTS[k]
                    ny = y + Tile.J_DISPLACEMENTS[k]
                    if 0 <= nx < size and 0 <= ny < size:
                        nb.append(nx * size + ny)
                table.append(tuple(nb))
        _NEIGHBOURS_CACHE[size] = table
    return _NEIGHBOURS_CACHE[size]


class HexBoard:
    __slots__ = ("size", "cells", "neighbours")

    def __init__(self, size: int = 11):
        self.size = size
        self.cells = [EMPTY] * (size * size)
        self.neighbours = _build_neighbours(size)

    # ---- conversion ----------------------------------------------------

    @classmethod
    def from_engine(cls, board: Board) -> "HexBoard":
        """Build a HexBoard from the engine's Board."""
        hb = cls(board.size)
        size = board.size
        for x, row in enumerate(board.tiles):
            for y, tile in enumerate(row):
                if tile.colour == Colour.RED:
                    hb.cells[x * size + y] = RED
                elif tile.colour == Colour.BLUE:
                    hb.cells[x * size + y] = BLUE
        return hb

    def to_index(self, x: int, y: int) -> int:
        return x * self.size + y

    def to_xy(self, cell: int) -> tuple[int, int]:
        return divmod(cell, self.size)

    def copy(self) -> "HexBoard":
        hb = HexBoard.__new__(HexBoard)
        hb.size = self.size
        hb.cells = self.cells[:]
        hb.neighbours = self.neighbours
        return hb

    # ---- moves ---------------------------------------------------------

    def legal_moves(self) -> list[int]:
        """Indices of all empty cells (swap is not included)."""
        return [i for i, v in enumerate(self.cells) if v == EMPTY]

    def is_empty(self, cell: int) -> bool:
        return self.cells[cell] == EMPTY

    def play(self, cell: int, player: int) -> None:
        """Place a stone. The caller must make sure the cell is empty."""
        self.cells[cell] = player

    def undo(self, cell: int) -> None:
        """Remove the stone at cell."""
        self.cells[cell] = EMPTY

    # ---- win detection -------------------------------------------------

    def _on_start_edge(self, cell: int, player: int) -> bool:
        if player == RED:
            return cell < self.size                 # x == 0
        return cell % self.size == 0                # y == 0

    def _on_end_edge(self, cell: int, player: int) -> bool:
        if player == RED:
            return cell >= self.size * (self.size - 1)  # x == size - 1
        return cell % self.size == self.size - 1        # y == size - 1

    def is_winning_move(self, cell: int, player: int) -> bool:
        """True if placing player's stone on the empty cell wins the game.

        Only searches the group the new stone would join, so it is much
        cheaper than a full-board winner() check.
        """
        cells = self.cells
        nbs = self.neighbours
        start = self._on_start_edge(cell, player)
        end = self._on_end_edge(cell, player)
        if start and end:  # only possible on a 1x1 board
            return True
        seen = {cell}
        stack = [cell]
        while stack:
            c = stack.pop()
            for n in nbs[c]:
                if n not in seen and cells[n] == player:
                    seen.add(n)
                    stack.append(n)
                    if not start and self._on_start_edge(n, player):
                        start = True
                    if not end and self._on_end_edge(n, player):
                        end = True
                    if start and end:
                        return True
        return False

    def has_won(self, player: int) -> bool:
        """True if player connects their two edges on the current board."""
        size = self.size
        cells = self.cells
        if player == RED:
            stack = [y for y in range(size) if cells[y] == RED]
        else:
            stack = [x * size for x in range(size) if cells[x * size] == BLUE]
        seen = set(stack)
        nbs = self.neighbours
        while stack:
            c = stack.pop()
            if self._on_end_edge(c, player):
                return True
            for n in nbs[c]:
                if n not in seen and cells[n] == player:
                    seen.add(n)
                    stack.append(n)
        return False

    def winner(self) -> int:
        """RED, BLUE, or EMPTY if nobody has won yet."""
        if self.has_won(RED):
            return RED
        if self.has_won(BLUE):
            return BLUE
        return EMPTY

    # ---- debugging -----------------------------------------------------

    def __str__(self) -> str:
        chars = {EMPTY: ".", RED: "R", BLUE: "B"}
        lines = []
        for x in range(self.size):
            row = " ".join(chars[self.cells[x * self.size + y]] for y in range(self.size))
            lines.append(" " * x + row)
        return "\n".join(lines)
