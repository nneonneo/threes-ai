''' Help the user achieve a high score in a real game of threes by using a move searcher.

This assistant remote-controls an Android device via ADB, playing the game without human intervention. '''

from adb_shell import ADBShell

import time
import os
import re

from ocr import ocr
from base_assistant import run_assistant

re_sshot = r'^S_(\d{6}).png$'
fmt_sshot = r'S_%06d.png'

def gen_board_mem(shell):
    from cStringIO import StringIO
    while True:
        sshot_data = shell.execute('screencap -p')
        sshot_file = StringIO(sshot_data)
        board, tile = ocr(sshot_file)
        yield board, tile, False

def gen_board_disk(shell, d, resume=False):
    curnum = 0
    if resume:
        imglist = sorted([fn for fn in os.listdir(d) if re.match(re_sshot, fn)])
        if imglist:
            last = imglist[-1]
            for fn in imglist:
                print fn
                board, tile = ocr(os.path.join(d, fn))
                skip = (fn != last)
                yield board, tile, skip
            curnum = int(re.match(re_sshot, last).group(1), 10)+1

    while True:
        sshot_data = shell.execute('screencap -p')
        fn = fmt_sshot % curnum
        dfn = os.path.join(d, fn)
        curnum += 1
        with open(dfn, 'wb') as f:
            f.write(sshot_data)
        print fn
        board, tile = ocr(dfn)
        yield board, tile, False

def make_move(move):
    print "Recommended move:", move
    os.system('say ' + move)
    time.sleep(2)

def rungame(args):
    d = args[0]
    if len(args) == 2:
        startpoint = os.path.basename(args[1])
    else:
        startpoint = None

    run_assistant(gen_board(d, startpoint), make_move)

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

    if args.outdir:
        try:
            os.makedirs(args.outdir)
        except OSError:
            pass
        run_assistant(gen_board_disk(shell, args.outdir, args.resume), make_move)
    else:
        run_assistant(gen_board_mem(shell), make_move)

if __name__ == '__main__':
    import sys
    exit(main(sys.argv[1:]))
