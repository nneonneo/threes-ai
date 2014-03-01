/* Define UNIF_RANDOM as a random number generator returning a value in [0..n-1].
 * 
 * If you don't have arc4random_uniform, try using a regular PRNG (like random()) mod n,
 * with added bias correction logic. */
#define UNIF_RANDOM(n) arc4random_uniform(n)

/* The fundamental trick: the 4x4 board is represented as a 64-bit word,
 * with each board square packed into a single 4-bit nibble.
 * 
 * The maximum possible board value that can be supported is 12288 (=15), but
 * this is a minor limitation. The highest tile in the game appears to be 6144.
 * 
 * The space and computation savings from using this representation should be significant.
 * 
 * The nibble shift can be computed as (r,c) -> shift (4*r + c). That is, (0,0) is the LSB.
 */

typedef uint64_t board_t;
typedef uint16_t row_t;

#define _BOARDCHR(v) ("0123456789abcdef"[(v)&0xf])
#define _ROWCHR(v) _BOARDCHR(v), _BOARDCHR((v)>>4), _BOARDCHR((v)>>8), _BOARDCHR((v)>>12)
#define BOARDSTR(board,sep) ((char []){_ROWCHR(board), sep, _ROWCHR((board)>>16), sep, _ROWCHR((board)>>32), sep, _ROWCHR((board)>>48), 0})
#define PRINTBOARD(board) printf("%s\n", BOARDSTR(board, '\n'))
#define ROW_MASK 0xFFFFULL
#define COL_MASK 0x000F000F000F000FULL

static inline row_t pack_col(board_t col) {
    return (row_t)(col | (col >> 12) | (col >> 24) | (col >> 36));
}

static inline board_t unpack_col(row_t row) {
    board_t tmp = row;
    return (tmp | (tmp << 12ULL) | (tmp << 24ULL) | (tmp << 36ULL)) & COL_MASK;
}

static inline row_t reverse_row(row_t row) {
    return (row >> 12) | ((row >> 4) & 0x00F0)  | ((row << 4) & 0x0F00) | (row << 12);
}


/* The tile deck */
typedef uint32_t deck_t;

#define DECK_SUB_1(deck) ((deck)-1)
#define DECK_SUB_2(deck) ((deck)-(1<<8))
#define DECK_SUB_3(deck) ((deck)-(1<<16))

#define DECK_1(deck) ((deck) & 0xff)
#define DECK_2(deck) (((deck) >> 8) & 0xff)
#define DECK_3(deck) (((deck) >> 16) & 0xff)
#define INITIAL_DECK (0x00040404UL) // four of each item

/* Extra deck bits for expectimax */
#define DECK_WITH_MAXVAL(deck,mv) (((deck) & 0xffffff) | (mv << 24))
#define DECK_MAXVAL(deck) (((deck) >> 24) & 0xff)

#define HIGH_CARD_FREQ 21

/* Functions */
#ifdef __cplusplus
extern "C" {
#endif

void init_score_tables(void);
void init_move_tables(void);

typedef int (*get_move_func_t)(board_t, deck_t, int);
int find_best_move(board_t board, deck_t deck, int tile);
int ask_for_move(board_t board, deck_t deck, int tile);
void play_game(get_move_func_t get_move);

#ifdef __cplusplus
}
#endif
