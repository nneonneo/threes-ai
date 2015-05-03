#include <stdlib.h>
#include "platdefs.h"

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

#define ROW_MASK 0xFFFFULL
#define COL_MASK 0x000F000F000F000FULL

static inline void print_board(board_t board) {
    int i,j;
    for(i=0; i<4; i++) {
        for(j=0; j<4; j++) {
            printf("%c", "0123456789abcdef"[(board)&0xf]);
            board >>= 4;
        }
        printf("\n");
    }
    printf("\n");
}

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
/* Candidate tileset */
typedef uint16_t tileset_t;

#define FOREACH_TILE(t,tileset) for(tileset_t _tmp = (tileset); t=ctz(_tmp), _tmp != 0; _tmp &= _tmp-1)

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

DLL_PUBLIC void set_heurweights(float *f, int flen);

DLL_PUBLIC void init_tables(void);

typedef int (*get_move_func_t)(board_t, deck_t, tileset_t);
DLL_PUBLIC float score_toplevel_move(board_t board, deck_t deck, tileset_t tileset, int move);
DLL_PUBLIC int find_best_move(board_t board, deck_t deck, tileset_t tileset);
DLL_PUBLIC int ask_for_move(board_t board, deck_t deck, tileset_t tileset);
DLL_PUBLIC void play_game(get_move_func_t get_move);

#ifdef __cplusplus
}
#endif
