class Namespace(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

CONFIGS = {
    # model_name: settings dictionary
    # sw,sh: screen size in pixels
    # x0,y0: top left corner of the first tile
    # w,h: size of the tile sample
    # dx,dy: spacing between adjacent tiles
    # tx,ty,tw,th: next-tile sample rectangle
    # sw,sh: screen width and height (set automatically)

    'LGE Nexus 5': Namespace(sw=1080, sh=1920, x0=141, y0=577,  w=144, h=112,  dx=219, dy=292,  tx=310, ty=128, tw=460, th=188),
    'OnePlus A0001': Namespace(sw=1080, sh=1920, x0=182, y0=608,  w=112, h=96,  dx=202.5, dy=270,  tx=330, ty=172, tw=440, th=174),
}
