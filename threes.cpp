#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <map>

#include "threes.h"

/* We can perform state lookups one row at a time by using arrays with 65536 entries. */

/* Move tables. Each row or compressed column is mapped to (oldrow^newrow) assuming row/col 0.
 *
 * Thus, the value is 0 if there is no move, and otherwise equals a value that can easily be
 * xor'ed into the current board state to update the board. */
static board_t row_left_table[65536];
static board_t row_right_table[65536];
static board_t col_up_table[65536];
static board_t col_down_table[65536];

void init_move_tables(void) {
    unsigned row;

    memset(row_left_table, 0, sizeof(row_left_table));
    memset(row_right_table, 0, sizeof(row_right_table));
    memset(col_up_table, 0, sizeof(col_up_table));
    memset(col_down_table, 0, sizeof(col_down_table));

    for(row = 0; row < 65536; row++) {
        unsigned int line[4] = {row & 0xf, (row >> 4) & 0xf, (row >> 8) & 0xf, (row >> 12) & 0xf};
        row_t result;
        int i, j;

        for(i=0; i<3; i++) {
            if(line[i] == 0) {
                line[i] = line[i+1];
                break;
            } else if(line[i] == 1 && line[i+1] == 2) {
                line[i] = 3;
                break;
            } else if(line[i] == 2 && line[i+1] == 1) {
                line[i] = 3;
                break;
            } else if(line[i] == line[i+1] && line[i] >= 3 && line[i] < 15) {
                line[i]++;
                break;
            }
        }

        if(i == 3)
            continue;

        /* fold to the left */
        for(j=i+1; j<3; j++)
            line[j] = line[j+1];
        line[3] = 0;

        result = (line[0]) | (line[1] << 4) | (line[2] << 8) | (line[3] << 12);

        row_left_table[row] = row ^ result;
        row_right_table[reverse_row(row)] = reverse_row(row) ^ reverse_row(result);
        col_up_table[row] = unpack_col(row) ^ unpack_col(result);
        col_down_table[reverse_row(row)] = unpack_col(reverse_row(row)) ^ unpack_col(reverse_row(result));
    }
}

#define DO_LINE(tbl,i,lookup,xv) do { \
        tmp = tbl[lookup]; \
        if(tmp) { \
            ch += 256 + (1 << i); \
            ret ^= xv; \
        } \
    } while(0)

#define DO_ROW(tbl,i) DO_LINE(tbl,i, (board >> (16*i)) & ROW_MASK,          tmp << (16*i))
#define DO_COL(tbl,i) DO_LINE(tbl,i, pack_col((board >> (4*i)) & COL_MASK), tmp << (4*i))

static inline board_t execute_move_0(board_t board, int *changed) {
    int ch = 0;
    board_t tmp;
    board_t ret = board;

    DO_COL(col_up_table, 0);
    DO_COL(col_up_table, 1);
    DO_COL(col_up_table, 2);
    DO_COL(col_up_table, 3);

    *changed = ch;
    return ret;
}

static inline board_t execute_move_1(board_t board, int *changed) {
    int ch = 0;
    board_t tmp;
    board_t ret = board;

    DO_COL(col_down_table, 0);
    DO_COL(col_down_table, 1);
    DO_COL(col_down_table, 2);
    DO_COL(col_down_table, 3);

    *changed = ch;
    return ret;
}

static inline board_t execute_move_2(board_t board, int *changed) {
    int ch = 0;
    board_t tmp;
    board_t ret = board;

    DO_ROW(row_left_table, 0);
    DO_ROW(row_left_table, 1);
    DO_ROW(row_left_table, 2);
    DO_ROW(row_left_table, 3);

    *changed = ch;
    return ret;
}

static inline board_t execute_move_3(board_t board, int *changed) {
    int ch = 0;
    board_t tmp;
    board_t ret = board;

    DO_ROW(row_right_table, 0);
    DO_ROW(row_right_table, 1);
    DO_ROW(row_right_table, 2);
    DO_ROW(row_right_table, 3);

    *changed = ch;
    return ret;
}
#undef DO_ROW
#undef DO_COL
#undef DO_LINE

/* Execute a move. Store status about the move's effects in `changed'.
 * 
 * The format of `changed' is (num_changed << 8) | changed_bits
 * where the ith bit of changed_bits is set iff row/col i moved.
 */
static inline board_t execute_move(int move, board_t board, int *changed) {
    switch(move) {
    case 0: // up
        return execute_move_0(board, changed);
    case 1: // down
        return execute_move_1(board, changed);
    case 2: // left
        return execute_move_2(board, changed);
    case 3: // right
        return execute_move_3(board, changed);
    default:
        return ~0ULL;
    }
}

static inline int get_max_rank(board_t board) {
    int maxrank = 0;
    while(board) {
        int k = board & 0xf;
        if(k > maxrank) maxrank = k;
        board >>= 4;
    }
    return maxrank;
}

/* Place a new tile on the board. Assumes the board is empty at the target location. */
static inline board_t insert_tile(int move, board_t board, int pos, int tile) {
    switch(move) {
    case 0: // up
        return board | (((board_t)tile) << (pos*4 + 48));
    case 1: // down
        return board | (((board_t)tile) << pos*4);
    case 2: // left
        return board | (((board_t)tile) << (12 + pos*16));
    case 3: // right
        return board | (((board_t)tile) << (pos*16));
    default:
        return ~0ULL;
    }
}


/* Optimizing the game */
static float row_heur_score_table[65536];
static float row_score_table[65536];

struct eval_state {
    std::map<board_t, float> trans_table; // transposition table, to cache previously-seen moves
    float cprob_thresh;
    int maxdepth;
    int curdepth;
    int cachehits;
    int moves_evaled;

    eval_state() : cprob_thresh(0), maxdepth(0), curdepth(0), cachehits(0), moves_evaled(0) {
    }
};

// score a single board heuristically
static float score_heur_board(board_t board);
// score a single board actually
static float score_board(board_t board);
// score over all possible moves
static float score_move_node(eval_state &state, board_t board, deck_t deck, float cprob);
// score over all possible tile choices
static float score_tilechoose_node(eval_state &state, board_t board, deck_t deck, float cprob, int move, int changed);
// score over all possible tile placements
static float score_tileinsert_node(eval_state &state, board_t board, deck_t deck, float cprob, int move, int changed, int tile);

void init_score_tables(void) {
    unsigned row;

    memset(row_heur_score_table, 0, sizeof(row_heur_score_table));
    memset(row_score_table, 0, sizeof(row_score_table));

    for(row = 0; row < 65536; row++) {
        int i;
        float heur_score = 0;
        float score = 0;

        for(i=0; i<4; i++) {
            int rank = (row >> (4*i)) & 0xf;

            if(rank == 0) {
                heur_score += 10000;
            } else if(rank >= 3) {
                //heur_score += powf(3, rank-2);
                score += powf(3, rank-2);
            }
        }
        row_score_table[row] = score;
        row_heur_score_table[row] = heur_score;
    }
}

#define SCORE_BOARD(board,tbl) ((tbl)[(board) & ROW_MASK] + \
    (tbl)[((board) >> 16) & ROW_MASK] + \
    (tbl)[((board) >> 32) & ROW_MASK] + \
    (tbl)[((board) >> 48) & ROW_MASK])

static float score_heur_board(board_t board) {
    return SCORE_BOARD(board, row_heur_score_table) + 100000;
}

static float score_board(board_t board) {
    return SCORE_BOARD(board, row_score_table);
}
    
static float score_tileinsert_node(eval_state &state, board_t board, deck_t deck, float cprob, int move, int changed, int tile) {
    float res = 0;
    float factor = 1.0f / (changed >> 8);
    int pos;
    cprob *= factor;
    for(pos=0; pos<4; pos++) {
        if(changed & (1<<pos))
            res += score_move_node(state, insert_tile(move, board, pos, tile), deck, cprob);
    }

    return res * factor;
}

static float score_tilechoose_node(eval_state &state, board_t board, deck_t deck, float cprob, int move, int changed) {
    float res = 0;
    int mv = DECK_MAXVAL(deck);

    if(!(deck & 0x00ffffff))
        deck = DECK_WITH_MAXVAL(INITIAL_DECK, mv);

    int a = DECK_1(deck);
    int b = DECK_2(deck);
    int c = DECK_3(deck);
    float div = a+b+c;
    float hres = 0;

    if(mv >= 7) {
        /* High tile */
        int choices = mv - 6;
        int i;

        for(i=0; i<choices; i++) {
            hres += score_tileinsert_node(state, board, deck, cprob / choices / HIGH_CARD_FREQ, move, changed, i+4);
        }
        hres /= (choices * HIGH_CARD_FREQ);

        div *= ((float)HIGH_CARD_FREQ)/(HIGH_CARD_FREQ - 1);
    }

    if(a)
        res += score_tileinsert_node(state, board, DECK_SUB_1(deck), cprob / div * a, move, changed, 1) * a;
    if(b)
        res += score_tileinsert_node(state, board, DECK_SUB_2(deck), cprob / div * b, move, changed, 2) * b;
    if(c)
        res += score_tileinsert_node(state, board, DECK_SUB_3(deck), cprob / div * c, move, changed, 3) * c;

    res /= div;
    res += hres;

    return res;
}

/* Statistics and controls */
// cprob: cumulative probability
/* don't recurse into a node with a cprob less than this threshold */
#define CPROB_THRESH_BASE (1e-3f)
#define CACHE_DEPTH_LIMIT 4

static float score_move_node(eval_state &state, board_t board, deck_t deck, float cprob) {
    if(cprob < state.cprob_thresh) {
        if(state.curdepth > state.maxdepth)
            state.maxdepth = state.curdepth;
        return score_heur_board(board);
    }

    if(state.curdepth < CACHE_DEPTH_LIMIT) {
        const auto &i = state.trans_table.find(board);
        if(i != state.trans_table.end()) {
            state.cachehits++;
            return i->second;
        }
    }

    int move;
    float best = 0;

    state.curdepth++;
    for(move=0; move<4; move++) {
        int changed;
        board_t newboard = execute_move(move, board, &changed);
        state.moves_evaled++;
        if(!changed)
            continue;

        float res = score_tilechoose_node(state, newboard, deck, cprob, move, changed);
        if(res > best)
            best = res;
    }
    state.curdepth--;

    if(state.curdepth < CACHE_DEPTH_LIMIT) {
        state.trans_table[board] = best;
    }

    return best;
}

static float _score_toplevel_move(eval_state &state, board_t board, deck_t deck, int tile, int move) {
    int changed;
    int maxrank = get_max_rank(board);
    board_t newboard = execute_move(move, board, &changed);

    if(!changed)
        return 0;

    deck = DECK_WITH_MAXVAL(deck, maxrank);
    state.cprob_thresh = CPROB_THRESH_BASE / (maxrank - 2);

    if(tile == 1)
        return score_tileinsert_node(state, newboard, DECK_SUB_1(deck), 1.0f, move, changed, 1);
    else if(tile == 2)
        return score_tileinsert_node(state, newboard, DECK_SUB_2(deck), 1.0f, move, changed, 2);
    else if(tile == 3)
        return score_tileinsert_node(state, newboard, DECK_SUB_3(deck), 1.0f, move, changed, 3);
    else {
        int choices = maxrank - 6;
        float highprob = 1.0f / choices;
        float res = 0;

        int card;

        for(card=0; card<choices; card++) {
            res += score_tileinsert_node(state, newboard, deck, highprob, move, changed, card+4);
        }

        return res * highprob;
    }
}

float score_toplevel_move(board_t board, deck_t deck, int tile, int move) {
    float res;
    struct timeval start, finish;
    double elapsed;
    eval_state state;

    gettimeofday(&start, NULL);
    res = _score_toplevel_move(state, board, deck, tile, move);
    gettimeofday(&finish, NULL);

    elapsed = (finish.tv_sec - start.tv_sec);
    elapsed += (finish.tv_usec - start.tv_usec) / 1000000.0;

    printf("Move %d: result %f: eval'd %d moves (%d cache hits, %zd cache size) in %.2f seconds (maxdepth=%d)\n", move, res,
        state.moves_evaled, state.cachehits, state.trans_table.size(), elapsed, state.maxdepth);

    return res;
}

/* Find the best move for a given board, deck and upcoming tile.
 * 
 * Note: the deck must represent the deck BEFORE the given tile was drawn.
 * This enables correct behaviour for 3+ tiles. */
int find_best_move(board_t board, deck_t deck, int tile) {
    int move;
    float best = 0;
    int bestmove = -1;

    printf("%s\n", BOARDSTR(board, '\n'));
    printf("Current scores: heur %.0f, actual %.0f\n", score_heur_board(board), score_board(board));
    printf("Next tile: %d (deck=%08x)\n", tile, deck);

    for(move=0; move<4; move++) {
        float res = score_toplevel_move(board, deck, tile, move);

        if(res > best) {
            best = res;
            bestmove = move;
        }
    }

    return bestmove;
}

int ask_for_move(board_t board, deck_t deck, int tile) {
    int move;
    char validstr[5];
    char *validpos = validstr;

    (void)deck;

    printf("%s\n", BOARDSTR(board, '\n'));

    for(move=0; move<4; move++) {
        int changed;
        execute_move(move, board, &changed);
        if(!changed)
            continue;
        *validpos++ = "UDLR"[move];
    }
    *validpos = 0;
    if(validpos == validstr)
        return -1;

    if(tile >= 3) {
        printf("Next tile: 3+\n");
    } else {
        printf("Next tile: %d\n", tile);
    }

    while(1) {
        char movestr[64];
        const char *allmoves = "UDLR";

        printf("Move [%s]? ", validstr);

        if(!fgets(movestr, sizeof(movestr)-1, stdin))
            return -1;

        if(!strchr(validstr, toupper(movestr[0]))) {
            printf("Invalid move.\n");
            continue;
        }

        return strchr(allmoves, toupper(movestr[0])) - allmoves;
    }
}

/* Playing the game */
static int draw_deck(deck_t *deck) {
    int a = DECK_1(*deck);
    int b = DECK_2(*deck);
    int c = DECK_3(*deck);
    int r = UNIF_RANDOM(a+b+c);

    if(r < a) {
        *deck = DECK_SUB_1(*deck);
        return 1;
    } else if(r-a < b) {
        *deck = DECK_SUB_2(*deck);
        return 2;
    } else {
        *deck = DECK_SUB_3(*deck);
        return 3;
    }
}

static board_t initial_board(deck_t *deck) {
    int i;
    board_t board = 0;

    /* Draw nine initial values */
    for(i=0; i<9; i++) {
        board |= ((board_t)draw_deck(deck)) << (4*i);
    }

    /* Shuffle the board (Fisher-Yates) */
    for(i=15; i>=1; i--) {
        int j = UNIF_RANDOM(i+1);
        board_t exc = ((board >> (4*i)) & 0xf) ^ ((board >> (4*j)) & 0xf);
        board ^= (exc << (4*i));
        board ^= (exc << (4*j));
    }

    return board;
}

void play_game(get_move_func_t get_move) {
    deck_t deck = INITIAL_DECK;
    board_t board = initial_board(&deck);
    int moveno = 0;

    while(1) {
        deck_t olddeck = deck;
        int i;
        int move;
        int tile;
        int changed;
        int maxrank = get_max_rank(board);

        if(!deck)
            olddeck = deck = INITIAL_DECK;

        if(maxrank >= 7 && UNIF_RANDOM(HIGH_CARD_FREQ) == 0) {
            tile = UNIF_RANDOM(maxrank-6) + 4;
        } else {
            tile = draw_deck(&deck);
        }

        printf("\nMove #%d\n", ++moveno);

        move = get_move(board, olddeck, tile);
        if(move < 0)
            break;

        board = execute_move(move, board, &changed);
        int count = changed >> 8;
        int choice = UNIF_RANDOM(count);
        for(i=0; i<4; i++) {
            if(changed & (1<<i)) {
                if(choice == 0)
                    break;
                choice--;
            }
        }

        board = insert_tile(move, board, i, tile);
    }

    printf("%s\n", BOARDSTR(board, '\n'));
    printf("\nGame over. Your score is %.0f. The highest rank you achieved was %d.\n", score_board(board), get_max_rank(board));
}

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    init_move_tables();
    init_score_tables();

    play_game(find_best_move);
    return 0;
}
