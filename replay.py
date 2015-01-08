''' Replay a move sequence with a particular random seed. '''

def replay(seed, moveseq):
    from threes import play_game, to_val, to_score
    from collections import Counter
    import random

    random.seed(seed)

    initial_deck = Counter([1,2,3]*4)
    deck = None
    game = play_game()
    moveseq = [None] + ['UDLR'.find(x) for x in moveseq]

    for moveno, move in enumerate(moveseq):
        m, tileset, valid = game.send(move)
        print to_val(m)
        if deck is None:
            deck = initial_deck.copy() - Counter(m.flatten())

        if not valid:
            print "Game over."
            break

        print 'next tile:', list(to_val(tileset))

        if tileset[0] <= 3:
            deck[tileset[0]] -= 1
        if all(deck[i] == 0 for i in (1,2,3)):
            deck = initial_deck.copy()

    print "Your score is", to_score(m).sum()
    return to_score(m).sum()

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print "Usage:", sys.argv[0], "<seed>", "<moveseq>"
        exit(-1)

    replay(int(sys.argv[1]), sys.argv[2])
