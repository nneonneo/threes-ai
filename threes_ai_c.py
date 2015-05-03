import ctypes
import numpy as np
import os
import sys

for suffix in ['so', 'dll', 'dylib']:
    dllfn = 'bin/threes.' + suffix
    if not os.path.isfile(dllfn):
        continue
    threes = ctypes.CDLL(dllfn)
    break
else:
    print("Couldn't find threes library bin/threes.{so,dll,dylib}! Make sure to build it first.")
    exit()

threes.init_tables()

threes.find_best_move.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint16]
threes.score_toplevel_move.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint16, ctypes.c_int]
threes.score_toplevel_move.restype = ctypes.c_float
threes.set_heurweights.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int]

MULTITHREAD = True

def get_c_state(m, deck, tileset):
    ''' Convert a NumPy board, dictionary deck, and tile set into C state variables. '''
    board = 0
    for i,v in enumerate(m.flatten()):
        board |= long(v) << (4*i)
    deck = (m.max() << 24) | (deck[1]) | (deck[2] << 8) | (deck[3] << 16)
    tileset = sum((1 << t) for t in tileset)
    return board, deck, tileset

if MULTITHREAD:
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(4)
    def score_toplevel_move(args):
        return threes.score_toplevel_move(*args)

    def find_best_move(m, deck, tileset):
        ''' Find the best move with the given board, deck and upcoming tile. '''
        board, deck, tileset = get_c_state(m, deck, tileset)

        scores = pool.map(score_toplevel_move, [(board, deck, tileset, move) for move in xrange(4)])
        # To minimize score:
        # bestmove, bestscore = min(enumerate(scores), key=lambda x:x[1] or 1e100)
        bestmove, bestscore = max(enumerate(scores), key=lambda x:x[1])
        return bestmove
else:
    def find_best_move(m, deck, tileset):
        ''' Find the best move with the given board, deck and upcoming tile. '''
        board, deck, tileset = get_c_state(m, deck, tileset)

        return threes.find_best_move(board, deck, tileset)

def set_heurweights(*args):
    f = (ctypes.c_float * len(args))(*args)
    threes.set_heurweights(f, len(args))
    threes.init_tables()

def play_with_search(verbose=True):
    from threes import play_game, to_val, to_score
    from collections import Counter

    import random
    import time
    seed = hash(str(time.time()))
    print "seed=%d" % seed
    random.seed(seed)

    initial_deck = Counter([1,2,3]*4)
    deck = None
    game = play_game()
    move = None

    moveno = 0
    while True:
        m, tileset, valid = game.send(move)
        if verbose:
            print to_val(m)
        if deck is None:
            deck = initial_deck.copy() - Counter(m.flatten())

        if not valid:
            break

        if verbose:
            print 'next tile:', list(to_val(tileset))

        move = find_best_move(m, deck, tileset)
        moveno += 1
        if verbose:
            print "Move %d: %s" % (moveno, ['up', 'down', 'left', 'right'][move])
        else:
            sys.stdout.write('UDLR'[move])
            sys.stdout.flush()

        if tileset[0] <= 3:
            deck[tileset[0]] -= 1
        if all(deck[i] == 0 for i in (1,2,3)):
            deck = initial_deck.copy()

    print
    print "Game over. Your score is", to_score(m).sum()
    return to_score(m).sum()

if __name__ == '__main__':
    play_with_search()
