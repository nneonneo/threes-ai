import numpy as np

def to_val(x):
    return np.where(x < 3, x, 3*2**(x-3))

def to_score(x):
    return np.where(x < 3, 0, 3**(x-2))

def find_fold(line):
    ''' find the position where the line folds, assuming it folds towards the left. '''
    for i in xrange(3):
        if line[i] == 0:
            return i
        elif (line[i], line[i+1]) in ((1,2), (2,1)):
            return i
        elif line[i] == line[i+1] and line[i] >= 3:
            return i
    return -1

def do_fold(line, pos):
    if line[pos] == 0:
        line[pos] = line[pos+1]
    elif line[pos] < 3:
        line[pos] = 3
    else:
        line[pos] += 1
    line[pos+1:-1] = line[pos+2:]
    line[-1] = 0
    return line

def get_lines(m, dir):
    if dir == 0: # up
        return [m[:,i] for i in xrange(4)]
    elif dir == 1: # down
        return [m[::-1,i] for i in xrange(4)]
    elif dir == 2: # left
        return [m[i,:] for i in xrange(4)]
    elif dir == 3: # right
        return [m[i,::-1] for i in xrange(4)]

TILESEQ = [3,2,3,1,1,1,3,1,2,2,1,2,1,3,1,2,3,3,2,1,2,3,1,1,2,2,3,1,1,2,3,2,3,3,3,2,1,2,3,2,1,1,3,2,2,3,2,1,3,1,1,3,2,2,2,2,1,1,1,3,1,3,3,3,1,1,1,1,2,1,3,3,2,1,1,3,3,3,1,3,2,2,1,2,2,1,2,2,1,3,2,3,3,1,1,1,2,3,2,3,2,1,1,2,2,2,2,1,2,3,2,1,3,1,1,2,3,3,2,2,1,2,3,1,2,2,2,1,1,2,2,2,2,3,1,2,2,3,2,3,2,2,2]
START = np.asarray([[0,  0,  0,  3],
[3,  2,  2,  1],
[3,  0,  0,  1],
[2,  0,  3,  0]])

def play_game():
    ''' Non-interactive play_game function. Yields (board, next_tile, valid_moves) tuples.
    Send your next move in via the generator .send.
    Raises StopIteration when the game is over.'''

    import random
    # TODO: Not sure how initial board is generated.
    #m = np.array([random.choice([0,0,1,2,3]) for _ in xrange(16)]).reshape(4,4)
    m = START.copy()

    moveno = 0
    while True:
        lineset = [get_lines(m, i) for i in xrange(4)]
        foldset = [[find_fold(l) for l in lineset[i]] for i in xrange(4)]
        valid = [i for i in xrange(4) if any(f >= 0 for f in foldset[i])]

        # TODO: figure out if the tiles are chosen with equal probability
        # TODO: figure out how the game picks tiles of value > 3
        #tile = random.choice([1,2,3])
        tile = TILESEQ[moveno % len(TILESEQ)]

        move = yield m, tile, valid
        moveno += 1

        if not valid:
            break

        folds = foldset[move]
        lines = lineset[move]
        changed = []
        for i in xrange(4):
            if folds[i] >= 0:
                do_fold(lines[i], folds[i])
                changed.append(i)
        insertline = random.choice(changed)
        lines[insertline][-1] = tile

def play_game_interactive():
    game = play_game()
    move = None

    while True:
        m, tile, valid = game.send(move)
        print to_val(m)

        if not valid:
            print "Game over."
            print "Your score is", to_score(m).sum()
            break
            
        print 'next tile:', {1: '1', 2: '2', 3: '3+'}[tile]

        movelist = ''.join('UDLR'[i] for i in valid)
        while True:
            move = raw_input('Move [%s]? ' % movelist).upper()
            if move not in movelist:
                print "Invalid move."
                continue
            move = 'UDLR'.find(move)
            break

if __name__ == '__main__':
    play_game_interactive()
