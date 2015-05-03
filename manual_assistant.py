''' Help the user achieve a high score in a real game of threes by using a move searcher.

This assistant takes manual input from the user, allowing it to be used with any game. '''

import os
import numpy as np
import re

from base_assistant import run_assistant, movenames
from threes import do_move, get_lines

def to_ind(val):
    try:
        return {0:0, 1:1, 2:2, 3:3, 6:4, 12:5, 24:6, 48:7, 96:8, 192:9, 384:10, 768:11, 1536:12, 3072:13, 6144:14}[val]
    except KeyError as e:
        raise Exception("Invalid value %s" % val)

class ManualAssistant:
    def __init__(self):
        self.last_board = None
        self.last_move = None

    def _ask_tileset(self):
        tileset = raw_input("Upcoming tile(s)? ")
        tileset = {'blue': '1', 'red': '2', 'white': '3+'}.get(tileset, tileset)
        if tileset in ('3+', '6+'):
            return tileset # will be fixed up
        tileset = re.split(r'[\s,]', tileset)
        return {to_ind(int(v)) for v in tileset}

    def _fixup_tileset(self, tileset, board):
        if tileset not in ('3+', '6+'):
            return tileset

        maxval = board.max()
        out = set(xrange(4, maxval-3))
        if tileset == '3+':
            out |= {3}
        else:
            out |= {4} # make sure the tileset isn't empty
        return out

    def _parse_delta(self, ind, val=None, move=None):
        if self.last_board is None:
            raise Exception("Can't specify a delta: last board is unknown")

        ind = int(ind)
        if val is None:
            if len(self.last_tiles) > 1:
                raise Exception("Can't omit tile value: multiple possible previous tiles")
            val = list(self.last_tiles)[0]
        else:
            val = to_ind(int(val))
            if val not in self.last_tiles:
                raise Exception("New tile wasn't in previous tile set")
            
        if move is None:
            move = self.last_move

        move = movenames.index(move)
        newboard = self.last_board.copy()
        changed = do_move(newboard, move)
        line = get_lines(newboard, move)[ind-1]
        if line[-1] != 0:
            raise Exception("Incorrect changed row/col")
        line[-1] = val
        return newboard

    def _parse_board(self, bits):
        out = np.array([to_ind(int(x)) if x else 0 for x in bits], dtype=int)
        return out.reshape((4,4))

    def _ask_board(self):
        if self.last_board is None:
            print "Current board?"
        else:
            print "Current board or difference from last board?"

        bits = []
        while 1:
            line = re.split(r'[ \t,]', raw_input())
            bits += line
            if 1 <= len(bits) < 4:
                return self._parse_delta(*bits)
            elif len(bits) == 16:
                return self._parse_board(bits)
            elif len(bits) > 16:
                raise Exception("More than 16 numbers specified!")

    def gen_board(self):
        while 1:
            while 1:
                try:
                    board = self._ask_board()
                    break
                except Exception as e:
                    print "Didn't understand your input:", e

            while 1:
                try:
                    tileset = self._ask_tileset()
                    break
                except Exception as e:
                    print "Didn't understand your input:", e

            tileset = self._fixup_tileset(tileset, board)
            yield board, tileset, False
            self.last_board = board
            self.last_tiles = tileset

    def make_move(self, move):
        print "*** Suggested move:", move
        print
        self.last_move = move

def parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Suggest moves for Threes!")

    args = parser.parse_args(argv)
    return args

def main(argv):
    from itertools import count
    args = parse_args(argv)

    print 'Welcome to the Threes! assistant. See README.md for help on input formats.'
    assistant = ManualAssistant()
    run_assistant(assistant.gen_board(), assistant.make_move, False)

if __name__ == '__main__':
    import sys
    exit(main(sys.argv[1:]))
