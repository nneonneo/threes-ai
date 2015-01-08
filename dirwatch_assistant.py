''' Help the user achieve a high score in a real game of threes by using a move searcher.

This assistant watches a directory of screenshot files, and makes a move when it detects a new screenshot. '''

import time
import os

from ocr import ocr
from base_assistant import run_assistant

def watchdir(d, sleeptime=0.1):
    base = set(os.listdir(d))
    while 1:
        time.sleep(sleeptime)
        new = set(os.listdir(d))
        for v in sorted(new - base):
            if not v.startswith('.'):
                yield os.path.join(d, v)
        base = new

def gen_board(d, startpoint=None):
    if startpoint is not None:
        for fn in os.listdir(d):
            if fn >= startpoint and not fn.startswith('.'):
                print fn
                fn = os.path.join(d, fn)
                board, tileset = ocr(fn)
                yield board, tileset, True

    for fn in watchdir(d):
        board, tileset = ocr(fn)
        print os.path.basename(fn)
        yield board, tileset, False

def make_move(move):
    print "Recommended move:", move
    os.system('say ' + move)

def rungame(args):
    d = args[0]
    if len(args) == 2:
        startpoint = os.path.basename(args[1])
    else:
        startpoint = None

    run_assistant(gen_board(d, startpoint), make_move)

if __name__ == '__main__':
    import sys
    rungame(sys.argv[1:])
