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

def make_deck():
    import random
    deck = [1]*4 + [2]*4 + [3]*4
    random.shuffle(deck)
    return deck

def play_game():
    ''' Non-interactive play_game function. Yields (board, next_tile, valid_moves) tuples.
    Send your next move in via the generator .send.
    Raises StopIteration when the game is over.'''

    import random

    deck = make_deck()
    pos = random.sample(xrange(16), 9)
    m = np.zeros((16,), dtype=int)
    m[pos] = deck[:len(pos)]
    deck = deck[len(pos):]
    m = m.reshape((4,4))

    while True:
        lineset = [get_lines(m, i) for i in xrange(4)]
        foldset = [[find_fold(l) for l in lineset[i]] for i in xrange(4)]
        valid = [i for i in xrange(4) if any(f >= 0 for f in foldset[i])]

        # TODO: check that this probability is correct
        maxval = m.max()
        if maxval >= 7 and random.random() < 1/24.:
            tile = random.choice(xrange(4, maxval-2))
        else:
            if not deck:
                deck = make_deck()
            tile = deck.pop()

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

        if tile >= 3:
            print 'next tile: 3+'
        else:
            print 'next tile:', tile

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
