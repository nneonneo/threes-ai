import PIL.Image as Image
import numpy as np
import os
import re

DNAME = os.path.dirname(__file__)

CONFIGS = {
    # (screen_width, screen_height): settings dictionary
    # x0,y0: top left corner of the first tile
    # w,h: size of the tile sample
    # dx,dy: spacing between adjacent tiles
    # tx,ty: next-tile sample point
    # sw,sh: screen width and height (set automatically)

    (640, 1136): dict(x0=92, y0=348,  w=96, h=80,  dx=120, dy=160,  tx=320, ty=146),    # Retina 4" iPhone/iPod
    (1080, 1920): dict(x0=155, y0=518,  w=162, h=135,  dx=202.5, dy=270,  tx=540, ty=222),    # Nexus 5
}

for w,h in CONFIGS:
    CONFIGS[w,h]['sw'] = w
    CONFIGS[w,h]['sh'] = h

def to_ind(val):
    return {0:0, 1:1, 2:2, 3:3, 6:4, 12:5, 24:6, 48:7, 96:8, 192:9, 384:10, 768:11, 1536:12, 3072:13, 6144:14}[val]

def to_imgkey(imc):
    return np.asarray(imc).tostring()

def get_exemplar_dir(cfg):
    return os.path.join(DNAME, 'exemplars', '%dx%d' % (cfg['sw'], cfg['sh']))

def get_exemplars(cfg):
    import glob
    for fn in glob.glob(os.path.join(get_exemplar_dir(cfg), '*.png')):
        val = re.findall(r'.*/(\d+).*\.png', fn)[0]
        yield int(val), Image.open(fn)

def load_exemplars(cfg):
    data = {}
    for val, im in get_exemplars(cfg):
        data[to_imgkey(im)] = val
    cfg['exemplars'] = data
    return data

def extract(cfg, im, r, c):
    x = cfg['x0'] + c*cfg['dx']
    y = cfg['y0'] + r*cfg['dy']

    return im.crop((int(x), int(y), int(x+cfg['w']), int(y+cfg['h'])))

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

def guess_classify(cfg, imc):
    THRESH = 10000
    possible = set()
    for val, im in get_exemplars(cfg):
        err = np.asarray(im).astype(float) - np.asarray(imc).astype(float)
        if 0 < np.abs(err).sum() < THRESH:
            possible.add(val)
    if len(possible) == 1:
        return possible.pop()
    elif len(possible) > 1:
        print "Warning: multiple matches %s; guesser may not be accurate!" % possible
    return None

def classify(cfg, imc):
    if 'exemplars' not in cfg:
        load_exemplars(cfg)
    exemplars = cfg['exemplars']

    key = to_imgkey(imc)
    val = exemplars.get(key, None)
    if val is not None:
        return val

    val = guess_classify(cfg, imc)
    if val is not None:
        print "Unrecognized object automatically classified as %d" % val
    else:
        imc.show()
        val = raw_input("\aUnrecognized object! Recognize it and type in the value: ")

    for i in xrange(1, 10000):
        fn = os.path.join(get_exemplar_dir(cfg), '%s.%d.png' % (val, i))
        if not os.path.isfile(fn):
            imc.save(fn)
            break
    else:
        print "Failed to save exemplar."
    exemplars = load_exemplars(cfg)
    return exemplars[key]

def find_next_tile(cfg, im):
    px = im.getpixel((cfg['tx'], cfg['ty']))[:3]
    ret = {
        (102, 204, 255): 1,
        (255, 102, 128): 2,
        (254, 255, 255): 3,
        (0, 0, 0): 4,
        (119, 126, 140): -1, # lose
    }.get(px, 0)
    if ret == 0:
        print "Warning: unknown next tile (px=%s)!" % (px,)
        im.show()
    return ret

def ocr(fn):
    im = Image.open(fn)
    cfg = config_for_image(im)

    tile = find_next_tile(cfg, im)
    if tile == 0:
        return None, tile

    out = np.zeros((4,4), dtype=int)

    for r in xrange(4):
        for c in xrange(4):
            imc = extract(cfg, im, r, c)
            out[r,c] = to_ind(classify(cfg, imc))

    return out, tile

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        print fn
        print ocr(fn)
        print
