import PIL.Image as Image
import numpy as np
import os
import re
import glob

DNAME = os.path.dirname(__file__)

class Namespace(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

CONFIGS = {
    # (screen_width, screen_height): settings dictionary
    # x0,y0: top left corner of the first tile
    # w,h: size of the tile sample
    # dx,dy: spacing between adjacent tiles
    # tx,ty,tw,th: next-tile sample rectangle
    # sw,sh: screen width and height (set automatically)

#    (640, 1136): Namespace(x0=92, y0=348,  w=96, h=80,  dx=120, dy=160,  tx=320, ty=146),    # Retina 4" iPhone/iPod # NEEDS tw,th
    (1080, 1920): Namespace(x0=141, y0=577,  w=144, h=112,  dx=219, dy=292,  tx=310, ty=128, tw=460, th=188),    # Nexus 5
}

def to_ind(val):
    return {0:0, 1:1, 2:2, 3:3, 6:4, 12:5, 24:6, 48:7, 96:8, 192:9, 384:10, 768:11, 1536:12, 3072:13, 6144:14}[val]

def to_imgkey(imc):
    return np.asarray(imc).tostring()

class ExemplarMatcher:
    def __init__(self, cfg, tag, thresh=500000):
        self.cfg = cfg
        self.tag = tag
        self.loaded = False
        self.exemplars = {}
        self.lastid = {}
        self.guess_thresh = thresh
        try:
            os.makedirs(self.exemplar_dir)
        except EnvironmentError:
            pass

    @property
    def exemplar_dir(self):
        return os.path.join(DNAME, 'exemplars', '%dx%d' % (self.cfg.sw, self.cfg.sh), self.tag)

    def get_exemplars(self):
        d = self.exemplar_dir
        for fn in os.listdir(d):
            m = re.match(r'^(.+)\.(\d+)\.png$', fn)
            if m:
                yield m.group(1), int(m.group(2)), Image.open(os.path.join(d, fn))

    def load(self):
        self.exemplars = {}
        for val, ind, im in self.get_exemplars():
            self.exemplars[to_imgkey(im)] = val
            self.lastid[val] = max(self.lastid.get(val, 0), ind)
        self.loaded = True

    def guess_classify(self, imc):
        possible = set()
        imcarr = np.asarray(imc).astype(float)
        for val, ind, im in self.get_exemplars():
            err = np.asarray(im).astype(float) - imcarr
            if 0 < np.abs(err).sum() < self.guess_thresh:
                possible.add(val)
        if len(possible) == 1:
            return possible.pop()
        elif len(possible) > 1:
            print "Warning: multiple matches %s; guesser may not be accurate!" % possible
        return None

    def classify(self, imc):
        if not self.loaded:
            self.load()

        key = to_imgkey(imc)
        val = self.exemplars.get(key, None)
        if val is not None:
            return val

        val = self.guess_classify(imc)
        if val is not None:
            print "Unrecognized %s automatically classified as %s" % (self.tag, val)
        else:
            imc.show()
            val = raw_input("\aUnrecognized %s! Recognize it and type in the value: " % self.tag)

        nid = self.lastid.get(val, 0) + 1
        imc.save(os.path.join(self.exemplar_dir, '%s.%d.png' % (val, nid)))
        self.exemplars[to_imgkey(imc)] = val
        self.lastid[val] = nid
        return val

for (w,h),cfg in CONFIGS.iteritems():
    cfg.sw = w
    cfg.sh = h
    cfg.next_matcher = ExemplarMatcher(cfg, 'next', 50000)
    cfg.tile_matcher = ExemplarMatcher(cfg, 'tile', 500000)

def extract_tile(cfg, im, r, c):
    x = cfg.x0 + c*cfg.dx
    y = cfg.y0 + r*cfg.dy

    return im.crop((int(x), int(y), int(x+cfg.w), int(y+cfg.h)))

def extract_next(cfg, im):
    return im.crop((cfg.tx, cfg.ty, cfg.tx + cfg.tw, cfg.ty + cfg.th))

def config_for_image(im):
    w,h = im.size
    if (w,h) not in CONFIGS:
        raise Exception("No OCR configuration for screen size %dx%d!" % (w,h))
    return CONFIGS[w,h]

def saveall(fn):
    im = Image.open(fn)
    cfg = config_for_image(im)
    fn, ext = os.path.splitext(fn)

    for r in xrange(4):
        for c in xrange(4):
            extract(cfg, im, r, c).save(fn + '-r%dc%d.png' % (r,c))

#saveall('sample/IMG_3189.PNG')

def ocr(fn):
    im = Image.open(fn)
    cfg = config_for_image(im)

    imc = extract_next(cfg, im)
    tileset = cfg.next_matcher.classify(imc)
    if tileset == 'gameover':
        return None, None
    tileset = [to_ind(int(t)) for t in tileset.split(',')]
    out = np.zeros((4,4), dtype=int)

    for r in xrange(4):
        for c in xrange(4):
            imc = extract_tile(cfg, im, r, c)
            out[r,c] = to_ind(int(cfg.tile_matcher.classify(imc)))

    return out, tileset

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        print fn
        print ocr(fn)
        print
