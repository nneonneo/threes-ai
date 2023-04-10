#!/usr/bin/env python3

''' Basic Python implementation of Threes! '''

import random
import sys

# https://github.com/nneonneo/threes-ai/blob/master/threes.py
__author__ = 'Robert Xiao <nneonneo@gmail.com>'

# modified by michaelroger

# Input keys for up, down, left right
MOVES='WSAD'

def list_to_val(l):
    return [ x if x < 3 else 3*(2**(x-3)) for x in l]

def to_val(table):
    # internal -> display
    # -------------------
    # 0 -> 0
    # 1 -> 1
    # 2 -> 2
    # 3 -> 0 
    # 4 -> 1
    # n -> 3^n-3
    return [ list_to_val(row) for row in table ]

def to_score(table):
    return [ 
              [ x if x < 3 else 3**(x-2) for x in row] for row in table
            ]

def find_fold(line):
    ''' find the position where the line folds (merges), assuming it folds towards the
    beginning. '''
    for i in range(3):
        if line[i] == 0 and line[i+1] > 0:
            return i
        elif (line[i], line[i+1]) in ((1,2), (2,1)):
            return i
        elif line[i] == line[i+1] and line[i] >= 3:
            return i
    return -1

def do_fold(line, pos):
    old_line = line[:]
    line = line[:]
    if line[pos] == 0:
        line[pos] = line[pos+1]
    elif line[pos] < 3:
        line[pos] = 3
    else:
        line[pos] += 1
    line[pos+1:-1] = line[pos+2:]
    line[-1] = 0
#    print("do_fold:" , old_line, pos, line)
    return line

def get_lines(m, dir):
    if dir == 0: # up
        return [[m[r][c] for r in range(4)] for c in range(4)]
    elif dir == 1: # down -- reverse of up
        return [[m[r][c] for r in range(4)][::-1] for c in range(4)]
    elif dir == 2: # left 
        return m
    elif dir == 3: # right -- reverse of left
        return [m[r][::-1] for r in range(4)]

# put get_lines back into matrix
def put_lines(m, dir):
    if dir == 0: # up
        return [[m[r][c] for r in range(4)] for c in range(4)]
    elif dir == 1: # down -- reverse of up
        return [[m[r][c] for r in range(4)] for c in range(4)][::-1]
    elif dir == 2: # left 
        return m
    elif dir == 3: # right -- reverse of left
        return [m[r][::-1] for r in range(4)]


def make_deck():
    import random
    deck = [1]*4 + [2]*4 + [3]*4
    random.shuffle(deck)
    return deck

def do_move(m, move, new_tileset):
    lines = get_lines(m, move)
    folds = [find_fold(l) for l in lines]
#    print ("folds: ", folds)
    changelines = []
    m = []
    for i in range(4):
        if folds[i] >= 0:
            new_line = do_fold(lines[i], folds[i])
            changelines.append(new_line)
        else:
            new_line = lines[i]
        m.append(new_line)
    random.choice(changelines)[-1] = random.choice(new_tileset)
    m = put_lines(m, move)
#    print("changelines: ", changelines)
    return m

def play_game():
    ''' Non-interactive play_game function. Yields (board, next_tile, valid_moves) tuples.
    Send your next move in via the generator .send.
    Raises StopIteration when the game is over.'''


    deck = make_deck()
    pos = random.sample(range(16), 9)
    m = []
    for r in range(4):
      m.append([])
      for c in range(4):
        m[r].append(0)

    for i in range(len(pos)):
      p = pos[i]
      m[p//4][p%4] = deck[i]
    deck = deck[len(pos):]

    while True:
        lineset = [get_lines(m, i) for i in range(4)]
        foldset = [[find_fold(l) for l in lineset[i]] for i in range(4)]
        valid = [i for i in range(4) if any(f >= 0 for f in foldset[i])]

        # TODO: Update random tile generation to account for new pick-three implementation
        maxval=0
        for row in m:
          for cell in row:
            maxval = max(maxval, cell)
        if maxval >= 7 and random.random() < 1/24.:
            if maxval <= 9:
                new_tileset = list(range(4, maxval-2))
            else:
                top = random.choice(range(6, maxval-2))
                new_tileset = list(range(top-2, top+1))
        else:
            if not deck:
                deck = make_deck()
            new_tileset = [deck.pop()]

        move = yield m, new_tileset, valid

        if not valid:
            break

        m = do_move(m, move, new_tileset)
        
class col:
    HEADER = '\033[95m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WARNING = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored(code, text): return code + text + col.END

SPRITES = {
        0: '    ',
        1:  colored(col.CYAN, '  1 '),
        2:  colored(col.RED, '  2 '),
        3:'  3 ', 4:'  6 ', 5:' 12 ', 6:' 24 ', 7:' 48 ', 8:' 96 ', 9:' 192',
        10: ' 384', 11: ' 768', 12: '1536', 13: '3072', 14: '6144',
        }

def line_to_str(l):
    return " ".join([SPRITES[x] for x in l])

def play_game_interactive():
    game = play_game()
    move = None
    m, new_tileset, valid = game.send(move)

    while True:
        print()
        print('next: ', line_to_str(new_tileset))
        print('---------------------')
        for line in m:
          print(line_to_str(line))

        if not valid:
            print()
            print("Game over.")
            sum = 0
            for row in to_score(m):
              for cell in row:
                  sum += cell
            print("Your score is", sum)
            break
        
        movelist = ''.join(MOVES[i] for i in valid)

        print()
        move_in = None
        while not move_in:
          move_in = input('Move [%s]? ' % movelist)
          move_char = move_in.upper()
          
        valid_move = move_char in movelist
        if not valid_move:
            print("Invalid move.")
            continue
        move = MOVES.find(move_char)
        print(move)
        m, new_tileset, valid = game.send(move)

# https://stackoverflow.com/questions/510357/how-to-read-a-single-character-from-the-user
class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try: self.impl = _GetchWindows()
        except ImportError: self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self): import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()
getch = _Getch()

# end https://stackoverflow.com/questions/510357/how-to-read-a-single-character-from-the-user


if __name__ == '__main__':
    play_game_interactive()