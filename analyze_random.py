from getmoves import getmove

if __name__ == '__main__':
    from ocr import ocr
    import glob

    files = glob.glob('ocr/sample-game/IMG_*.PNG')
    files.sort()

    boards = []
    for fn in files:
        boards.append(ocr(fn))

    m0 = boards[0][0]
    print m0

    counts = {1:(m0==1).sum(), 2:(m0==2).sum(), 3:(m0==3).sum()}

    for i in xrange(len(boards)-1):
        ot = boards[i][1]
        counts[ot] += 1

        move, t = getmove(boards[i][0], boards[i+1][0])
        print boards[i][0].max(), move, t, ot, counts
