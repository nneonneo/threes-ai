import PIL.Image as Image
import numpy as np
import os
import re

DNAME = os.path.dirname(__file__)

def to_ind(val):
    return {0:0, 1:1, 2:2, 3:3, 6:4, 12:5, 24:6, 48:7, 96:8, 192:9, 384:10, 768:11, 1536:12, 3072:13}[val]

def to_imgkey(imc):
    return np.asarray(imc).tostring()

def load_exemplars():
    import glob
    data = {}
    for fn in glob.glob(os.path.join(DNAME, 'exemplars', '*.png')):
        val = re.findall(r'.*/(\d+).*\.png', fn)[0]
        data[to_imgkey(Image.open(fn))] = int(val)
    return data

def extract(im, r, c):
    x0, y0 = 92, 348
    w, h = 96, 80
    dx, dy = 120, 160

    x = x0 + c*dx
    y = y0 + r*dy

    return im.crop((x, y, x+w, y+h))

def saveall(fn):
    im = Image.open(fn)
    fn, ext = os.path.splitext(fn)

    for r in xrange(4):
        for c in xrange(4):
            extract(im, r, c).save(fn + '-r%dc%d.png' % (r,c))

#saveall('sample/IMG_3189.PNG')
exemplars = load_exemplars()

def classify(imc):
    global exemplars

    key = to_imgkey(imc)
    val = exemplars.get(key, None)
    if val is not None:
        return val

    imc.show()
    vst = raw_input("Unrecognized object! Recognize it and type in the value: ")
    for i in xrange(1, 1000):
        fn = os.path.join(DNAME, 'exemplars', '%s.%d.png' % (vst, i))
        if not os.path.isfile(fn):
            imc.save(fn)
            break
    else:
        print "Failed to save exemplar."
    exemplars = load_exemplars()
    return exemplars[key]

def find_next_tile(im):
    px = im.getpixel((320, 146))
    ret = {
        (102, 204, 255): 1,
        (255, 102, 128): 2,
        (254, 255, 255): 3,
        (0, 0, 0): 4}.get(px, 0)
    if ret == 0:
        print "Warning: unknown next tile (px=%s)!" % (px,)
        im.show()
    return ret

def ocr(fn):
    im = Image.open(fn)

    out = np.zeros((4,4), dtype=int)

    for r in xrange(4):
        for c in xrange(4):
            imc = extract(im, r, c)
            out[r,c] = to_ind(classify(imc))

    return out, find_next_tile(im)

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        print fn
        print ocr(fn)
        print
