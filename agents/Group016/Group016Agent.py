from random import choice

from agents.Group016.board import HexBoard, colour_to_player, opponent
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move


class Group016Agent(AgentBase):
    """Week 1 baseline for Group016.

    Each turn:
    1. On turn 2 (only possible as player 2), swap with a 50% chance.
    2. If a move wins immediately, play it.
    3. If the opponent could win with their next move, block that cell.
    4. Otherwise, play a random empty cell.

    The board logic (legal moves, win detection) lives in board.py so that the
    decision step can be replaced by the team's chosen algorithm later.
    """

    def __init__(self, colour: Colour):
        super().__init__(colour)

    def make_move(self, turn: int, board: Board, opp_move: Move | None) -> Move:
        if turn == 2 and choice([0, 1]) == 1:
            return Move(-1, -1)

        hb = HexBoard.from_engine(board)
        # read the colour every turn: a swap changes it
        me = colour_to_player(self.colour)
        opp = opponent(me)
        moves = hb.legal_moves()

        for player in (me, opp):
            for cell in moves:
                if hb.is_winning_move(cell, player):
                    return Move(*hb.to_xy(cell))

        return Move(*hb.to_xy(choice(moves)))
