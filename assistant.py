''' Help the user achieve a high score in a real game of threes by using a move searcher. '''

import time
import os
from collections import Counter

from ocr import ocr
from getmoves import getmove
from threes import to_score, to_val
from threes_ai_c import find_best_move

def watchdir(d, sleeptime=0.1):
    base = set(os.listdir(d))
    while 1:
        time.sleep(sleeptime)
        new = set(os.listdir(d))
        for v in sorted(new - base):
            if not v.startswith('.'):
                yield os.path.join(d, v)
        base = new

def initial_deck():
    return Counter([1]*4 + [2]*4 + [3]*4)

def movename(move):
    return ['up', 'down', 'left', 'right'][move]

def step(fn, board, deck):
    newboard, tile = ocr(fn)
    if deck is None:
        deck = initial_deck() - Counter(newboard.flatten())
        return newboard, deck, tile

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

    return newboard, deck, tile

def rungame(args):
    board = None
    deck = None
    moveno = 0

    d = args[0]
    if len(args) == 2:
        startpoint = os.path.basename(args[1])
        for fn in os.listdir(d):
            if fn >= startpoint and not fn.startswith('.'):
                fn = os.path.join(d, fn)
                print
                print os.path.basename(fn)
                print "Move number", moveno+1
                moveno += 1
                board, deck, tile = step(fn, board, deck)

    for fn in watchdir(d):
        print
        print os.path.basename(fn)
        print "Move number", moveno+1
        moveno += 1
        board, deck, tile = step(fn, board, deck)

        print to_val(board)
        print "Current score:", to_score(board).sum()
        print "Next tile: %d (deck=1:%d, 2:%d, 3:%d)" % (tile, deck[1], deck[2], deck[3])

        move = find_best_move(board, deck, tile)
        if move < 0:
            break
        print "Recommended move:", movename(move)
        os.system('say ' + movename(move))

if __name__ == '__main__':
    import sys
    rungame(sys.argv[1:])
