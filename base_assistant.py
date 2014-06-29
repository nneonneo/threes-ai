''' Base functions for move assistants. '''

from threes import *
from collections import Counter
from threes_ai_c import find_best_move

__author__ = 'Robert Xiao <nneonneo@gmail.com>'

def getmove(m1, m2):
    ''' Find the move and new tile which transforms board m1 to m2.

    Returns (move, tile) or None if it cannot be determined uniquely. '''

    possible = []

    for move in xrange(4):
        m = m1.copy()

        lines = get_lines(m, move)
        folds = [find_fold(l) for l in lines]

        if all(f < 0 for f in folds):
            continue

        for i in xrange(4):
            if folds[i] >= 0:
                do_fold(lines[i], folds[i])

        diff = m2[m != m2]
        if len(diff) != 1:
            continue

        # check that the inserted value aligns with a fold
        lines2 = get_lines(m2, move)
        for i in xrange(4):
            if folds[i] < 0:
                continue
            if lines[i][-1] != lines2[i][-1]:
                break
        else:
            # insertion doesn't correspond to a fold point
            continue

        possible.append((move, diff[0]))

    if len(possible) == 0:
        print "Warning: impossible situation"
    elif len(possible) > 1:
        print "Warning: ambiguous result"
    else:
        return possible[0]

def initial_deck():
    return Counter([1]*4 + [2]*4 + [3]*4)

def movename(move):
    return 

def _step(board, deck, newboard):
    if deck is None:
        deck = initial_deck() - Counter(newboard.flatten())
        return newboard, deck

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

    return newboard, deck

def run_assistant(gen_board, make_move_func):
    ''' Run the assistant.
    
    gen_board: A generator which returns (board, next_tile, skip_move) tuples.
        If skip_move is True, the assistant will not calculate or make a move.
    make_move_func: A function to call which will make the recommended move.
    '''

    board = None
    deck = None
    moveno = 0
    movenames = ['up', 'down', 'left', 'right']

    for newboard, tile, skip_move in gen_board:
        print
        print "Move number", moveno+1
        moveno += 1

        board, deck = _step(board, deck, newboard)

        print to_val(board)
        print "Current score:", to_score(board).sum()
        print "Next tile: %d (deck=1:%d, 2:%d, 3:%d)" % (tile, deck[1], deck[2], deck[3])

        if not skip_move:
            move = find_best_move(board, deck, tile)
            if move < 0:
                break
            make_move_func(movenames[move])

if __name__ == '__main__':
    # A simple demonstration/test of getmove
    from ocr import ocr
    import glob

    files = glob.glob('ocr/sample-game/IMG_*.PNG')
    files.sort()

    boards = []
    for fn in files:
        boards.append(ocr(fn))

    for i in xrange(len(boards)-1):
        print getmove(boards[i][0], boards[i+1][0]), boards[i][1]
