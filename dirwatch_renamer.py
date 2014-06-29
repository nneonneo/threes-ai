''' Rename files from one directory to another as they come in.

This is useful for renaming files from a new DCIM folder to an older one, which
may be necessary if the DCIM folder changes during an assisted run.
'''

import os
import shutil
import time

__author__ = 'Robert Xiao <nneonneo@gmail.com>'

def watchdir(d, sleeptime=0.1):
    base = set()
    while 1:
        time.sleep(sleeptime)
        new = set(os.listdir(d))
        for v in sorted(new - base):
            if not v.startswith('.'):
                yield os.path.join(d, v)
        base = new

if __name__ == '__main__':
    import sys
    d1, d2 = sys.argv[1:]
    for fn in watchdir(d1):
        dfn = os.path.join(d2, os.path.basename(fn))
        print '%s -> %s' % (fn, dfn)
        try:
            os.rename(fn, os.path.join(d2, os.path.basename(fn)))
        except (IOError, OSError):
            bfn = os.path.join(d2, '.copy_tmp.' + os.path.basename(fn))
            shutil.move(fn, bfn)
            os.rename(bfn, dfn)
