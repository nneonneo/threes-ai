''' Help the user achieve a high score in a real game of threes by using a move searcher. '''

import ctypes
import time
import os
from collections import Counter

from ocr import ocr
from getmoves import getmove

threes = ctypes.CDLL('bin/threes.dylib')
threes.init_move_tables()
threes.init_score_tables()

threes.find_best_move.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]

def find_best_move(m, deck, tile):
    board = 0
    for i,v in enumerate(m.flatten()):
        board |= v << (4*i)
    deck = (m.max() << 24) | (deck[1]) | (deck[2] << 8) | (deck[3] << 16)

    return threes.find_best_move(board, deck, tile)

def watchdir(d, sleeptime=0.1):
    base = set(os.listdir(d))
    while 1:
        time.sleep(sleeptime)
        new = set(os.listdir(d))
        for v in sorted(new - base):
            yield os.path.join(d, v)
        base = new

def initial_deck():
    return Counter([1]*4 + [2]*4 + [3]*4)

def movename(move):
    return ['up', 'down', 'left', 'right'][move]

def rungame(d):
    deck = None

    for moveno, fn in enumerate(watchdir(d)):
        print
        print "Move number", moveno+1

        newboard, tile = ocr(fn)
        if deck is None:
            deck = initial_deck() - Counter(newboard.flatten())
        else:
            if all(v == 0 for v in deck.values()):
                deck = initial_deck()
            move, t = getmove(board, newboard)
            print "Previous move:", movename(move)
            if t <= 3:
                if deck[t] == 0:
                    raise Exception("Deck desynchronization detected!")
                deck[t] -= 1
            if all(v == 0 for v in deck.values()):
                deck = initial_deck()
        move = find_best_move(newboard, deck, tile)
        if move < 0:
            break
        print "Recommended move:", movename(move)
        os.system('say ' + movename(move))
        board = newboard

if __name__ == '__main__':
    import sys
    rungame(sys.argv[1])
