import os
import sys
from collections import Counter, deque
import functools
from itertools import ifilterfalse
import contextlib
import wave
import numpy as np
import subprocess

@contextlib.contextmanager
def redirect_stdout(f):
    '''Redirect stdout to file, f
    arguments:
    f -- File object to redirect stdout to.
    '''
    old_stdout = sys.stdout
    sys.stdout = f
    try:
        yield
    finally:
        sys.stdout = old_stdout

def lru_cache(maxsize=100):
    '''Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    '''
    maxqueue = maxsize * 10
    def decorating_function(user_function,
            len=len, iter=iter, tuple=tuple, sorted=sorted, KeyError=KeyError):
        cache = {}                  # mapping of args to results
        queue = deque() # order that keys have been used
        refcount = Counter()        # times each key is in the queue
        sentinel = object()         # marker for looping around the queue
        kwd_mark = object()         # separate positional and keyword args

        # lookup optimizations (ugly but fast)
        queue_append, queue_popleft = queue.append, queue.popleft
        queue_appendleft, queue_pop = queue.appendleft, queue.pop

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            # cache key records both positional and keyword args
            key = args
            if kwds:
                key += (kwd_mark,) + tuple(sorted(kwds.items()))

            # record recent use of this key
            queue_append(key)
            refcount[key] += 1

            # get cache entry or compute if not found
            try:
                result = cache[key]
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                cache[key] = result
                wrapper.misses += 1

                # purge least recently used cache entry
                if len(cache) > maxsize:
                    key = queue_popleft()
                    refcount[key] -= 1
                    while refcount[key]:
                        key = queue_popleft()
                        refcount[key] -= 1
                    cache.pop(key, None)
                    del refcount[key]

            # periodically compact the queue by eliminating duplicate keys
            # while preserving order of most recent access
            if len(queue) > maxqueue:
                refcount.clear()
                queue_appendleft(sentinel)
                for key in ifilterfalse(refcount.__contains__,
                                        iter(queue_pop, sentinel)):
                    queue_appendleft(key)
                    refcount[key] = 1


            return result

        def clear():
            cache.clear()
            queue.clear()
            refcount.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper
    return decorating_function

if os.isatty(sys.stderr.fileno()):
    def get_term_cols():
        '''Returns the number of columns in a terminal window'''
        try:
            txt = subprocess.check_output(['stty', 'size'], stderr=open('/dev/null', 'w'))
            ret = int(txt.strip().split()[1])
            if ret:
                return ret
        except Exception:
            pass

        try:
            ret = int(os.environ['COLUMNS'])
            if ret:
                return ret
        except Exception:
            pass

        try:
            txt = subprocess.check_output(['tput', 'cols'], stderr=open('/dev/null', 'w'))
            ret = int(txt.strip())
            if ret:
                return ret
        except Exception:
            pass

        return 80

    COLUMNS = get_term_cols()
    
    def printline(line, eol=False):
        '''Prints a line of text to a single line in a terminal, re-using the line'''
        sys.stderr.write('{:<{cols}}\r'.format(line, cols=COLUMNS-1))
        if eol:
            sys.stderr.write('\n')
        sys.stderr.flush()
else:
    def printline(line, eol=False):
        if eol:
            print line

def say(text):
    if sys.platform == 'darwin':
        subprocess.call(['say', text], stderr=open('/dev/null', 'w'))

def readwav(fn, wavchan=None):
    ''' read a 16-bit PCM WAVE file as a Numpy array '''
    # wave.open should support contexts :(
    with contextlib.closing(wave.open(fn)) as f:
        frames = f.readframes(f.getnframes())
    if wavchan is None:
        return np.frombuffer(frames, '<i2')
    else:
        return np.frombuffer(frames, '<i2')[wavchan::f.getnchannels()]

def parse_dir(dirname):
    '''Parses a directory that contains fingersense data'''
    app, timestamp, classlabel = dirname.split('-')
    return (app, timestamp, classlabel)

def get_arg(args, name, default=None):
    '''Get an argument from an argument dictionary or argparse.Namespace.
    Return default if the argument is not found, or is None.'''
    if args is None:
        return default
    try:
        res = getattr(args, name, default)
    except AttributeError:
        res = args.get(name, default)
    if res is None:
        return default
    return res

def fmt_argv_arg(arg):
    if "'" in arg or '"' in arg or ' ' in arg or '\\' in arg:
        return repr(arg)
    return arg
