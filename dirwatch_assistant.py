''' Help the user achieve a high score in a real game of threes by using a move searcher.

This assistant watches a directory of screenshot files, and makes a move when it detects a new screenshot. '''

import time
import os

from ocr import OCR
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

def gen_board(ocr, d, startpoint=None):
    if startpoint is not None:
        for fn in os.listdir(d):
            if fn >= startpoint and not fn.startswith('.'):
                print fn
                fn = os.path.join(d, fn)
                board, tileset = ocr.ocr(fn)
                yield board, tileset, True

    for fn in watchdir(d):
        board, tileset = ocr.ocr(fn)
        print os.path.basename(fn)
        yield board, tileset, False

def make_move(move):
    print "Recommended move:", move
    os.system('say ' + move)

def rungame(args):
    model = args.pop(0)
    d = args.pop(0)
    if args:
        startpoint = os.path.basename(args[0])
    else:
        startpoint = None

    run_assistant(gen_board(OCR(model), d, startpoint), make_move)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print "Usage:", sys.argv[0], "model", "directory", "[startpoint]"
        exit()
    rungame(sys.argv[1:])
