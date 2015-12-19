''' Help the user achieve a high score in a real game of threes by using a move searcher.

This assistant remote-controls http://play.threesgame.com, playing the game without human intervention. '''

import time
import os
import re
from cStringIO import StringIO

from base_assistant import run_assistant, movenames
from threes import do_move, to_val
import numpy as np

def to_ind(val):
    return {0:0, 1:1, 2:2, 3:3, 6:4, 12:5, 24:6, 48:7, 96:8, 192:9, 384:10, 768:11, 1536:12, 3072:13, 6144:14}[val]

class KeyboardWebAssistant:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.setup()

    def execute(self, cmd):
        return self.ctrl.execute(cmd)

    def setup(self):
        # Obtain a reference to the game objects by temporarily hijacking requestAnimationFrame
        self.ctrl.execute('''
        var _raf_tmp = window.requestAnimationFrame;
        window.requestAnimationFrame = function(f) { window.ThreesWebCore = f.scope; _raf_tmp.apply(this, arguments); }
        ''')

        while self.execute("typeof(window.ThreesWebCore)") == 'undefined':
            time.sleep(0.01)

        self.execute('''
        window.requestAnimationFrame = _raf_tmp;
        window.ThreesState = window.ThreesWebCore.app.host.game.__class__.state;
        window.ThreesGame = window.ThreesState._states.get("game");
        0;
        ''')

    def send_key_event(self, action, key):
        # Use generic events for compatibility with Chrome, which (for inexplicable reasons) doesn't support setting keyCode on KeyboardEvent objects.
        # See http://stackoverflow.com/questions/8942678/keyboardevent-in-chrome-keycode-is-0.
        return self.execute('''
            var keyboardEvent = document.createEventObject ? document.createEventObject() : document.createEvent("Events");
            if(keyboardEvent.initEvent)
                keyboardEvent.initEvent("%(action)s", true, true);
            keyboardEvent.keyCode = %(key)s;
            keyboardEvent.which = %(key)s;
            var element = document.body || document;
            element.dispatchEvent ? element.dispatchEvent(keyboardEvent) : element.fireEvent("on%(action)s", keyboardEvent);
            ''' % locals())

    def send_keypress(self, key):
        self.send_key_event('keydown', key)
        time.sleep(0.01)
        self.send_key_event('keyup', key)
        time.sleep(0.02)

    def get_state(self):
        return self.execute('''window.ThreesGame.__class__.state''')[0]

    def gen_board(self):
        while True:
            board = self.execute('''
            window.ThreesGame.grid.map(function(t) { return t.value; });
            ''')
            # Convert board values to ranks
            board = map(to_ind, board)
            # Reverse rows (the grid data starts at the bottom left
            board = np.array(board).reshape((4, 4))[::-1, :]

            toptile = self.execute('''window.ThreesGame.futureValue''')
            # This is not cheating: the actual tile is chosen randomly in onSpawn
            if toptile <= 3:
                tileset = {toptile}
            else:
                # next tile is chosen from at most 3 tiles below & including "toptile"
                tileset = {max(6, toptile/i) for i in (1, 2, 4)}
            tileset = set(map(to_ind, tileset))

            # check for gameover
            if self.get_state() in ('LOST', 'MENU'):
                tileset = None

            yield board, tileset, False

    def make_move(self, move):
        key = {'up': 38, 'down': 40, 'left': 37, 'right': 39}[move]
        self.send_keypress(key)

    def restart(self):
        ''' Restart from the "out of moves" screen '''
        while self.get_state() == 'LOST':
            # Just keep swiping
            self.send_keypress(38) # up
            time.sleep(0.2)

        while self.get_state() == 'MENU':
            self.send_keypress(32)
            time.sleep(0.2)

        self.send_keypress(32) # space

def parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Control Threes! running on an Android phone")
    parser.add_argument('--no-resume', action='store_false', dest='resume', default=True, help="Don't resume from previous data")
    parser.add_argument('--from-start', action='store_true', default=False, help="Assume that the game starts from the initial state. May improve performance.")
    parser.add_argument('--repeat', action='store_true', default=False, help="Repeat games indefinitely")
    parser.add_argument('-p', '--port', help="Port number to control on (default: 32000 for Firefox, 9222 for Chrome)", type=int)
    parser.add_argument('-b', '--browser', help="Browser you're using. Only Firefox with the Remote Control extension, and Chrome with remote debugging, are supported right now.", default='firefox', choices=('firefox', 'chrome'))

    args = parser.parse_args(argv)
    return args

def main(argv):
    from itertools import count
    args = parse_args(argv)

    if args.browser == 'firefox':
        from ffctrl import FirefoxRemoteControl
        if args.port is None:
            args.port = 32000
        ctrl = FirefoxRemoteControl(args.port)
    elif args.browser == 'chrome':
        from chromectrl import ChromeDebuggerControl
        if args.port is None:
            args.port = 9222
        ctrl = ChromeDebuggerControl(args.port)

    assistant = KeyboardWebAssistant(ctrl)

    if args.repeat:
        iterations = count(1)
    else:
        iterations = ['']

    for i,suffix in enumerate(iterations):
        if i >= 1:
            assistant.restart()
        run_assistant(assistant.gen_board(), assistant.make_move, args.from_start)

if __name__ == '__main__':
    import sys
    exit(main(sys.argv[1:]))
