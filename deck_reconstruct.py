# Reconstruct the deck state as the game plays out.
# This enables strong AI play from arbitrary starting positions.

from itertools import product

class DeckReconstructor:
    def __init__(self, board):
        ''' Initialize the deck reconstruction using the given board. '''
        self.candidates = []
        vals = list(board.flatten())
        ones = vals.count(1)
        twos = vals.count(2)
        for deck in product(xrange(5), repeat=3):
            if deck[0] == deck[1] == deck[2] == 0:
                continue

            if deck[0]+ones == deck[1]+twos:
                self.candidates.append(list(deck))

    def update(self, tile):
        ''' Update candidates using the tile that just spawned '''
        if tile > 3:
            return
        tile -= 1
        newcands = []
        for d in self.candidates:
            d[tile] -= 1
            if d[tile] < 0:
                continue
            if d[0] == d[1] == d[2] == 0:
                d = [4,4,4]
            newcands.append(d)
        self.candidates = newcands

    def __getitem__(self, i):
        if not (1 <= i <= 3):
            raise KeyError(i)
        if len(self.candidates) < 1:
            raise Exception("Deck state is invalid.")
        elif len(self.candidates) == 1:
            return self.candidates[0][i-1]

        # Assume all current candidates are equally likely
        s = sum(c[i-1] for c in self.candidates)
        n = len(self.candidates)
        return int(round(float(s)/n))

    def __self__(self):
        return "<DeckReconstructor, n=%d, avgdeck={1:%d, 2:%d, 3:%d}>" % (len(self.candidates), self[1], self[2], self[3])

    def __repr__(self):
        return "<DeckReconstructor, candidates=%s>" % self.candidates

if __name__ == '__main__':
    # simple test sequence
    import sys, os
    dirname, startfn = sys.argv[1:]

    deck = None
    from ocr import OCR
    ocr = OCR("LGE Nexus 5")
    imglist = sorted([fn for fn in os.listdir(dirname) if fn >= startfn])
    for fn in imglist:
        print fn
        board, tileset = ocr.ocr(os.path.join(dirname, fn))
        if deck is None:
            deck = DeckReconstructor(board)
        deck.update(tileset[0])
        print deck
