''' Crude pure-Python expectimax AI for Threes! '''

from threes import *
from utils import lru_cache

__author__ = 'Robert Xiao <nneonneo@gmail.com>'

def score_board(m):
    return to_score(m).sum() / ((m > 0).sum() ** 2.)

def expect_move_tile(m, move, tile, depth):
    lines = get_lines(m, move)
    folds = [find_fold(l) for l in lines]

    changed = []
    for i in xrange(4):
        if folds[i] >= 0:
            do_fold(lines[i], folds[i])
            changed.append(i)

    score = 0
    for choice in changed:
        mm = m.copy()
        mm[choice][-1] = tile
        _, sc = max_move(mm, None, depth)
        score += sc

    return float(score) / len(changed)

def expect_move(m, move, depth):
    if depth == 0:
        return score_board(m)

    score = 0

    # todo: model tile choice better
    # todo: figure out distribution for 3+s
    for tile in [1,2,3]:
        mm = m.copy()
        score += expect_move_tile(mm, move, tile, depth)

    return score / 3.0

def max_move(m, tile, depth):
    ''' Return the best move and score for a given board.
    
    m: board
    tile: next tile that will be placed (None if not known)
    depth: search depth (# of moves)
    '''

    if depth == 0:
        return None, score_board(m)

    bestscore = -1e10
    bestmove = None
    for move in xrange(4):
        mm = m.copy()

        lines = get_lines(mm, move)
        folds = [find_fold(l) for l in lines]
        if all(folds[i] < 0 for i in xrange(4)):
            continue

        if tile is None:
            score = expect_move(mm, move, depth-1)
        else:
            score = expect_move_tile(mm, move, tile, depth-1)
        if score > bestscore:
            bestmove = move
            bestscore = score

    return bestmove, bestscore

def play_with_search():
    game = play_game()
    move = None

    while True:
        m, tile, valid = game.send(move)
        print to_val(m)
        print 'current heuristic score:', score_board(m)

        if not valid:
            print "Game over."
            print "Your score is", to_score(m).sum()
            break

        print 'next tile:', {1: '1', 2: '2', 3: '3+'}[tile]
        move, score = max_move(m, tile, 3)
        print 'executing move:', move, 'score:', score

if __name__ == '__main__':
    play_with_search()
