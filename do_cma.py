import cma
import threes_ai_c
import numpy as np

# static float SCORE_MONOTONICITY_POWER = 4.0f;
# static float SCORE_MONOTONICITY_WEIGHT = 47.0f;
# static float SCORE_SUM_POWER = 3.5f;
# static float SCORE_SUM_WEIGHT = 11.0f;
# static float SCORE_MERGES_WEIGHT = 700.0f;
# static float SCORE_12_MERGES_WEIGHT = 700.0f;
# static float SCORE_EMPTY_WEIGHT = 270.0f;

# weights from the 2048 AI
# x0 = np.asarray((4.0, 47.0, 3.5, 11.0, 700.0, 270.0))
# sigma0 = 1.0

# best weights found by first CMA-ES optimization
# x0_scaled = np.asarray((2.91095798048, 1.97322364298, 1.48440229638, 1.09747286946, 2.9608468539, 2.12275763339))
# sigma0 = 0.711489393676

# best weights found by second CMA-ES optimization
x0_scaled = np.asarray((2.88734532873, 2.7658329942, 1.01944491674, 0.825579254038, 2.94556333483, 2.94556333483, 1.86127118327))
sigma0 = 1.0 #0.456169174299

# scale to convert normalized CMA-ES values into heuristic weights
scale = np.asarray((1.0, 25.0, 1.0, 50.0, 200.0, 200.0, 200.0))

def objective(x):
    y = x * scale
    threes_ai_c.set_heurweights(*y)
    result = 0
    for i in xrange(10):
        print "SETTINGS %s RUN %d" % (list(y), i+1)
        result += threes_ai_c.play_with_search(verbose=False)
    return -result

cma.fmin(objective, x0_scaled, sigma0)
