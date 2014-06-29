''' adb shell wrapper.

Compatible with Python 2.6, 2.7 and Python 3.'''

from subprocess import Popen, PIPE
import fcntl
import os
import time
import errno
import sys
import re
import select
from signal import SIGHUP
try:
    from pipes import quote as shellquote
except ImportError:
    from shlex import quote as shellquote
import select

__author__ = 'Robert Xiao <nneonneo@gmail.com>'

def read_timed(f, n=None, timeout=None):
    if timeout is None:
        res = select.select([f.fileno()], [], [])
    else:
        res = select.select([f.fileno()], [], [], timeout)

    if not res:
        return ''

    if n is None:
        return f.read()
    else:
        return f.read(n)

def read_nonblock(f, n=None):
    try:
        if n is None:
            return f.read()
        else:
            return f.read(n)
    except IOError as e:
        if e.errno == errno.EAGAIN:
            return ''
        else:
            raise

def warn(x):
    sys.stderr.write('Warning: %s\n' % x)
    sys.stderr.flush()

class ShellCommandException(OSError):
    def __init__(self, status, msg):
        self.status = status
        self.msg = msg
        self.args = (status, msg)

class ADBShell:
    def __init__(self, opts=None):
        # Module objects are deleted at shutdown; retain a SIGHUP reference
        # so we can use it in __del__.
        self.SIGHUP = SIGHUP

        cmd = ['adb']
        if opts:
            cmd.extend(opts)
        cmd += ['shell']

        self.proc = Popen(cmd, stdin=PIPE, stdout=PIPE)
        fd = self.proc.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        prompt = b''
        start = time.time()
        while time.time() - start < 0.5:
            s = read_nonblock(self.proc.stdout)
            if not s:
                res = self.proc.poll()
                if res is not None:
                    raise OSError("Failed to start '%s': process returned %d" % (' '.join(cmd), res))
                time.sleep(0.01)
                continue
            prompt += s
            if prompt.endswith(b'$ ') or prompt.endswith(b'# '):
                break
        else:
            if prompt:
                warn("nonstandard prompt %r" % prompt.decode())
            else:
                warn("timed out waiting for prompt!")

        m = re.match(br'^(\w+)@(\w+):(.*?) ([$#]) $', prompt)
        if m:
            self.user = m.group(1).decode()
            self.host = m.group(2).decode()
            self.cwd = m.group(3).decode()
            self.hash = m.group(4).decode()
            self.prompt = prompt
            self.prompt_re = re.compile((r'(?:(?P<status>\d+)\|)?(?P<user>%s|root)@%s:(?P<cwd>.*?) (?P<hash>[$#]) $' % (self.user, self.host)).encode())
        else:
            self.user = self.host = self.cwd = None
            for hash in [b'#', b'$']:
                if prompt.endswith(hash + b' '):
                    self.hash = hash
                    self.prompt_re = re.compile(re.escape(prompt[:-2]) + br'(?:(?P<status>\d+)\|)?(?P<hash>[$#]) $')
            else:
                self.hash = None
                self.prompt_re = re.compile(re.escape(prompt) + '$')
                # Already warned about this prompt.

            if len(prompt) != 2:
                warn("unparsed prompt %r" % prompt.decode())

            self.prompt = prompt

    def __del__(self):
        # Can also write '\n~.', a magic ssh-derived sequence that causes an immediate disconnect.
        self.proc.send_signal(self.SIGHUP)

    def _wait_for_echo(self, cmd):
        # Assume PS2="> "
        expected = re.sub(br'[\r\n]', br'\r\r\n> ', cmd) + b'\r\r\n'

        collected = bytearray()
        while len(collected) < len(expected):
            s = read_timed(self.proc.stdout, timeout=0.5)
            if not s:
                raise IOError("timed out waiting for shell echo")
            collected.extend(s)

        if collected[:len(expected)] != expected:
            warn("expected %r, got %r" % (collected[:len(expected)], expected))
        else:
            del collected[:len(expected)]

        return collected

    def execute(self, cmd):
        ''' Run the specified command through the shell and return the result.
        
        Raises ShellCommandException if the command returns an error code.'''

        if isinstance(cmd, list):
            cmd = ' '.join(shellquote(c) for c in cmd)
        cmd = cmd.encode().strip(b'\r').strip(b'\n')
        if b'\n' in cmd or b'\r' in cmd:
            warn("newline in command: results may not be correct")
        self.proc.stdin.write(cmd + b'\n')
        self.proc.stdin.flush()

        collected = self._wait_for_echo(cmd)

        while True:
            m = re.search(self.prompt_re, collected)
            if m:
                break
            s = read_timed(self.proc.stdout, timeout=None)
            collected.extend(s)

        ret = collected[:m.start()].replace(b'\r\n', b'\n')

        d = m.groupdict()
        if d.get('status'):
            raise ShellCommandException(int(d['status']), ret.decode())

        # Update prompt data
        for key in ['user', 'host', 'cwd', 'hash']:
            if key in d:
                setattr(self, key, d[key].decode())

        return ret
