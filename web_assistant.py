''' Help the user achieve a high score in a real game of Threes in your browser by using a move searcher.

This assistant remote-controls a Threes webpage, playing the game without human intervention.

Current Threes implementations supported:

- http://threesjs.com (unofficial fan-made version)
- http://play.threesgame.com (official port made by Threes! devs)
'''

from __future__ import print_function
import time
import os
import re
import json

from base_assistant import run_assistant, movenames
from threes import do_move, to_val
import numpy as np

def to_ind(val):
    return {0:0, 1:1, 2:2, 3:3, 6:4, 12:5, 24:6, 48:7, 96:8, 192:9, 384:10, 768:11, 1536:12, 3072:13, 6144:14}[val]

class WebAssistant:
    ''' General utilities for a web assistant '''
    
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.setup()

    def execute(self, cmd):
        return self.ctrl.execute(cmd)

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

    def setup(self):
        pass

    def gen_board(self):
        raise NotImplementedError()

    def make_move(self, move):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

class ThreesJSAssistant(WebAssistant):
    ''' Remote control http://threesjs.com '''
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.setup()

    def _is_game_over(self):
        return self.execute('$(".endgame").length') > 0

    def gen_board(self):
        while True:
            board = self.execute('''
            var board = [];
            for(var i=0; i<16; i++) {
                board.push(0);
            }
            $(".board .tile").each(function(i, e) {
                var pos = e.getAttribute("data-coords");
                var ind = Number(pos[0]) * 4 + Number(pos[1]);
                board[ind] = Number(e.innerText);
            });
            JSON.stringify(board);
            ''')
            # Convert board values to ranks
            board = list(map(to_ind, json.loads(board)))
            board = np.array(board).reshape((4, 4))

            nextTile = self.execute('''
            $(".next .tile").attr("class");
            ''')

            if 'blue' in nextTile:
                tileset = {1}
            elif 'red' in nextTile:
                tileset = {2}
            else:
                # next tile chosen from any tile in {3, maxtile}
                tileset = set()
                maxtile = board.max()
                n = 3
                while n <= max(maxtile / 8, 3):
                    tileset.add(n)
                    n *= 2
            print("possible tiles are %s" % tileset)

            tileset = set(map(to_ind, tileset))

            # check for gameover
            if self._is_game_over():
                tileset = None

            yield board, tileset, False

    def make_move(self, move):
        key = {'up': 38, 'down': 40, 'left': 37, 'right': 39}[move]
        self.execute('document.THREE.game.move({which: %d})' % key)
        time.sleep(0.5)

    def restart(self):
        self.send_keypress(13) # ENTER, to dismiss end-of-game dialog
        self.execute('document.THREE.game.new_game()')

class ThreesGameAssistant(WebAssistant):
    ''' Remote control http://play.threesgame.com '''

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

    def get_state(self):
        return self.execute('''window.ThreesGame.__class__.state''')[0]

    def gen_board(self):
        while True:
            board = self.execute('''
            JSON.stringify(window.ThreesGame.grid.map(function(t) { return t.value; }));
            ''')
            # Convert board values to ranks
            board = list(map(to_ind, json.loads(board)))
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

def guessWebImplementation(ctrl):
    ''' Try to sniff what Threes implementation we're playing on.

    We don't use the URL - that way, we can support compatible clones. '''
    if ctrl.execute('typeof(document.THREE)') != 'undefined':
        # threesjs.com
        return ThreesJSAssistant
    elif ctrl.execute('document.getElementById("device")') is not None:
        # play.threesgame.com (official implementation)
        return ThreesGameAssistant
    else:
        raise ValueError("Not yet able to support remote control of " + ctrl.execute('"" + window.location'))

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

    assistantClass = guessWebImplementation(ctrl)
    assistant = assistantClass(ctrl)

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
