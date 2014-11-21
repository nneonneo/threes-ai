import cma
import threes_ai_c
import numpy as np

# static float SCORE_MONOTONICITY_POWER = 4.0f;
# static float SCORE_MONOTONICITY_WEIGHT = 47.0f;
# static float SCORE_SUM_POWER = 3.5f;
# static float SCORE_SUM_WEIGHT = 11.0f;
# static float SCORE_MERGES_WEIGHT = 700.0f;
# static float SCORE_EMPTY_WEIGHT = 270.0f;

# weights from the 2048 AI
x0 = np.asarray((4.0, 47.0, 3.5, 11.0, 700.0, 270.0))
scale = np.asarray((1.0, 25.0, 1.0, 50.0, 200.0, 200.0))

def objective(x):
    y = x * scale
    threes_ai_c.set_heurweights(*y)
    result = 0
    for i in xrange(10):
        print "SETTINGS %s RUN %d" % (list(y), i+1)
        result += threes_ai_c.play_with_search()
    return -result

cma.fmin(objective, x0 / scale, 1.0)
