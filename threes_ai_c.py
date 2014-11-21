import ctypes
import numpy as np
import os

threes = ctypes.CDLL(os.path.join(os.path.dirname(__file__), 'bin', 'threes.dylib'))
threes.init_tables()

threes.find_best_move.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_int]
threes.score_toplevel_move.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_int, ctypes.c_int]
threes.score_toplevel_move.restype = ctypes.c_float
threes.set_heurweights.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int]

MULTITHREAD = True

def get_c_state(m, deck):
    ''' Convert a NumPy board and a dictionary deck into C state variables. '''
    board = 0
    for i,v in enumerate(m.flatten()):
        board |= v << (4*i)
    deck = (m.max() << 24) | (deck[1]) | (deck[2] << 8) | (deck[3] << 16)
    return board, deck

if MULTITHREAD:
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(4)
    def score_toplevel_move(args):
        return threes.score_toplevel_move(*args)

    def find_best_move(m, deck, tile):
        ''' Find the best move with the given board, deck and upcoming tile. '''
        board, deck = get_c_state(m, deck)

        scores = pool.map(score_toplevel_move, [(board, deck, tile, move) for move in xrange(4)])
        bestmove, bestscore = max(enumerate(scores), key=lambda x:x[1])
        return bestmove
else:
    def find_best_move(m, deck, tile):
        ''' Find the best move with the given board, deck and upcoming tile. '''
        board, deck = get_c_state(m, deck)

        return threes.find_best_move(board, deck, tile)

def set_heurweights(*args):
    f = (ctypes.c_float * len(args))(*args)
    threes.set_heurweights(f, len(args))
    threes.init_tables()

def play_with_search():
    from threes import play_game, to_val, to_score
    from collections import Counter

    initial_deck = Counter([1,2,3]*4)
    deck = None
    game = play_game()
    move = None

    moveno = 0
    while True:
        m, tile, valid = game.send(move)
        #print to_val(m)
        if deck is None:
            deck = initial_deck.copy() - Counter(m.flatten())

        if not valid:
            print "Game over."
            print "Your score is", to_score(m).sum()
            return to_score(m).sum()

        '''
        if tile > 3:
            print 'next tile: 6+'
            tile = 4
        else:
            print 'next tile:', tile
        '''

        move = find_best_move(m, deck, tile)
        moveno += 1
        print "Move %d: %s" % (moveno, ['up', 'down', 'left', 'right'][move])

        if tile <= 3:
            deck[tile] -= 1
        if all(deck[i] == 0 for i in (1,2,3)):
            deck = initial_deck.copy()

if __name__ == '__main__':
    play_with_search()
