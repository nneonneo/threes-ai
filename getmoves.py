''' Figure out the moves executed given a sequence of boards. '''

from threes import *

__author__ = 'Robert Xiao <nneonneo@gmail.com>'

def getmove(m1, m2):
    ''' return (move, tile) or None if it cannot be determined uniquely '''

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

if __name__ == '__main__':
    # A simple demonstration/test of getmoves
    from ocr import ocr
    import glob

    files = glob.glob('ocr/sample-game/IMG_*.PNG')
    files.sort()

    boards = []
    for fn in files:
        boards.append(ocr(fn))

    for i in xrange(len(boards)-1):
        print getmove(boards[i][0], boards[i+1][0]), boards[i][1]
