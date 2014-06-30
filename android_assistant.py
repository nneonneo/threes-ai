''' Help the user achieve a high score in a real game of threes by using a move searcher.

This assistant remote-controls an Android device via ADB, playing the game without human intervention. '''

from adb_shell import ADBShell

import time
import os
import re

from ocr import ocr
from base_assistant import run_assistant, movenames
from android_inputemu import get_ident, playback_gesture
from threes import do_move

re_sshot = r'^S_(\d{6}).png$'
fmt_sshot = r'S_%06d.png'

class AndroidAssistant:
    def __init__(self, shell, ident):
        self.shell = shell
        self.ident = ident
        self.last_board = None

    def gen_board_mem(self):
        from cStringIO import StringIO
        while True:
            sshot_data = self.shell.execute('screencap -p')
            sshot_file = StringIO(sshot_data)
            board, tile = ocr(sshot_file)
            self.last_board = board
            yield board, tile, False

    def gen_board_disk(self, d, resume=False):
        curnum = 0
        if resume:
            imglist = sorted([fn for fn in os.listdir(d) if re.match(re_sshot, fn)])
            if imglist:
                last = imglist[-1]
                for fn in imglist:
                    print fn
                    board, tile = ocr(os.path.join(d, fn))
                    skip = (fn != last)
                    self.last_board = board
                    yield board, tile, skip
                curnum = int(re.match(re_sshot, last).group(1), 10)+1

        while True:
            sshot_data = self.shell.execute('screencap -p')
            fn = fmt_sshot % curnum
            dfn = os.path.join(d, fn)
            curnum += 1
            with open(dfn, 'wb') as f:
                f.write(sshot_data)
            print fn
            board, tile = ocr(dfn)
            self.last_board = board
            yield board, tile, False

    def make_move(self, move):
        playback_gesture(self.shell, self.ident, move)

        sleeptime = 1.0
        if self.last_board is not None:
            board = self.last_board.copy()
            do_move(board, movenames.index(move))
            top = board.max()
            if sorted(self.last_board.flatten()) == sorted(board.flatten()):
                # No new tiles at all: no flipping or jumping
                sleeptime = 0.3
            elif top <= 3 or list(self.last_board.flatten()).count(top) == list(board.flatten()).count(top):
                # No new high tile created, so no jumping will occur.
                sleeptime = 0.5
            else:
                # The new high tile will jump; wait for a long time for jump animation to finish.
                sleeptime = 1.0

        time.sleep(sleeptime)

def parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Control Threes! running on an Android phone")
    parser.add_argument('--no-resume', action='store_false', dest='resume', default=True, help="Don't resume from previous data")
    parser.add_argument('outdir', nargs='?', help="Output directory for screen captures")

    args = parser.parse_args(argv)
    return args

def main(argv):
    args = parse_args(argv)

    shell = ADBShell()
    ident = get_ident(shell)

    assistant = AndroidAssistant(shell, ident)

    if args.outdir:
        try:
            os.makedirs(args.outdir)
        except OSError:
            pass
        run_assistant(assistant.gen_board_disk(args.outdir, args.resume), assistant.make_move)
    else:
        run_assistant(assistant.gen_board_mem(), assistant.make_move)

if __name__ == '__main__':
    import sys
    exit(main(sys.argv[1:]))
