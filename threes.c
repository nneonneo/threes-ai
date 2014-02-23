#include <ctype.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

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

static void init_move_tables(void) {
    unsigned row;

    memset(row_left_table, 0, sizeof(row_left_table));
    memset(row_right_table, 0, sizeof(row_right_table));
    memset(col_up_table, 0, sizeof(col_up_table));
    memset(col_down_table, 0, sizeof(col_down_table));

    for(row = 0; row < 65536; row++) {
        unsigned char line[4] = {row & 0xf, (row >> 4) & 0xf, (row >> 8) & 0xf, (row >> 12) & 0xf};
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

/* Execute a move. Store status about the move's effects in `changed'.
 * 
 * The format of `changed' is (num_changed << 8) | changed_bits
 * where the ith bit of changed_bits is set iff row/col i moved.
 */
static inline board_t execute_move(int move, board_t board, int *changed) {
    board_t tmp;
    board_t ret = board;

    *changed = 0;

#define DO_ROW(tbl,i) do { tmp = tbl[(board >> (16*i)) & ROW_MASK]; \
    if(tmp) { *changed |= 1 << i; *changed += 256; } \
    ret ^= (tmp << (16*i)); } while(0)

#define DO_COL(tbl,i) do { tmp = tbl[pack_col((board >> (4*i)) & COL_MASK)]; \
    if(tmp) { *changed |= 1 << i; *changed += 256; } \
    ret ^= (tmp << (4*i)); } while(0)

    switch(move) {
    case 0: // up
        DO_COL(col_up_table, 0);
        DO_COL(col_up_table, 1);
        DO_COL(col_up_table, 2);
        DO_COL(col_up_table, 3);
        break;
    case 1: // down
        DO_COL(col_down_table, 0);
        DO_COL(col_down_table, 1);
        DO_COL(col_down_table, 2);
        DO_COL(col_down_table, 3);
        break;
    case 2: // left
        DO_ROW(row_left_table, 0);
        DO_ROW(row_left_table, 1);
        DO_ROW(row_left_table, 2);
        DO_ROW(row_left_table, 3);
        break;
    case 3: // right
        DO_ROW(row_right_table, 0);
        DO_ROW(row_right_table, 1);
        DO_ROW(row_right_table, 2);
        DO_ROW(row_right_table, 3);
        break;
    default:
        return ~0ULL;
    }

#undef DO_ROW
#undef DO_COL

    return ret;
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
        return board | ((board_t)tile) << (pos*4 + 48);
    case 1: // down
        return board | ((board_t)tile) << pos*4;
    case 2: // left
        return board | ((board_t)tile) << (12 + pos*16);
    case 3: // right
        return board | ((board_t)tile) << (pos*16);
    default:
        return ~0ULL;
    }
}


/* Playing the game */
static int draw_deck(deck_t *deck) {
    int a = DECK_1(*deck);
    int b = DECK_2(*deck);
    int c = DECK_3(*deck);
    int r = UNIF_RANDOM(a+b+c);

    if(r < a) {
        DECK_SUB_1(*deck);
        return 1;
    } else if(r-a < b) {
        DECK_SUB_2(*deck);
        return 2;
    } else {
        DECK_SUB_3(*deck);
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

static void play_game_interactive(void) {
    deck_t deck = INITIAL_DECK;
    board_t board = initial_board(&deck);
    int tile;

    while(1) {
        int i;
        int changed;
        int maxrank = get_max_rank(board);
        char validstr[5];
        char *validpos = validstr;
        int move;

        printf("%s\n", BOARDSTR(board, '\n'));

        for(i=0; i<4; i++) {
            execute_move(i, board, &changed);
            if(!changed)
                continue;
            *validpos++ = "UDLR"[i];
        }
        *validpos = 0;
        if(validpos == validstr) {
            /* Game over: no valid moves left */
            break;
        }       

        if(maxrank >= 7 && UNIF_RANDOM(24) == 0) {
            tile = UNIF_RANDOM(maxrank-6) + 4;
        } else {
            if(!deck)
                deck = INITIAL_DECK;
            tile = draw_deck(&deck);
        }

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
                return;

            if(!strchr(validstr, toupper(movestr[0]))) {
                printf("Invalid move.\n");
                continue;
            }

            move = strchr(allmoves, toupper(movestr[0])) - allmoves;
            break;
        }

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

    printf("Game over.\n");
}

int main(int argc, char **argv) {
    init_move_tables();

    play_game_interactive();
    return 0;
}
