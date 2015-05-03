# About

AI for the game Threes! by Sirvo LLC. You can get the game from here: http://asherv.com/threes/

Building this AI was the inspiration for my later [2048 AI](https://github.com/nneonneo/2048-ai), and some of the ideas from the 2048 AI have been backported to this AI as well.

While I have not formally benchmarked the performance of this AI (yet), I know that it has successfully attained the 6144 tile multiple times, which is the highest tile available in the game. (Higher tiles are possible but unlikely, due to heavy random effects). The top score (at time of writing) is 775,524 points:

![775524 points](http://imgur.com/IaTPZyo.png)

This AI is a lot more experimental than its newer sibling 2048 AI because of the increased complexity of Threes! and because it has not received as much development time. Furthermore, Threes! is in general a bit of a moving target as the random tile generation algorithms are occasionally tweaked, necessitating changes in the AI.

# Algorithm

The algorithm for this AI is already essentially detailed in [this StackOverflow answer](http://stackoverflow.com/a/22498940/1204143) describing my 2048 AI. In essence, it implements a highly-optimized bruteforce search over the game tree (all possible moves, tile spawn values and tile values), using expectimax optimization to combine the results and find the "best" possible move.

This Threes AI is actually more sophisticated than the 2048 AI in a number of ways: most notably, it accounts for the "deck" of upcoming tiles (the well-documented process by which the random incoming tiles are selected), and it properly handles all the possible tile spawn locations based on the moves that are made. In short: this Threes AI correctly (to the best of my knowledge) emulates every detail of the Threes game as part of the expectimax optimization process.

# Building

Right now the AI only builds out-of-the-box on OS X. It will build on Linux, Unix and Cygwin with a bit more work. Notably, the code requires C++11, and the `UNIF_RANDOM` function should be replaced by a platform-specific uniform random number function (since `arc4random_uniform` is only available on BSD).

Simply run `make` to build the C++ components of the AI.

## Python prerequisites

You'll need Python 2.7, NumPy and PIL to run the Python programs.

## Running the command-line version

Run `bin/threes` if you want to see the AI by itself in action.

# Playing the game

## Android assistant
There are some web-based versions of Threes, but I wanted to make the AI play against the real app. So, I built an "assistant" program for Android devices, called `android_assistant.py`, which communicates with the phone over ADB and makes moves completely automatically. It requires only USB ADB permissions (standard developer access), and does not require rooting or any other modification of the device or app. It uses the standard Android `screencap` utility to obtain the (visible) game state, computes the optimal move, then uses the Linux input event subsystem to generate swipe events.

To use `android_assistant.py`, you will need to configure the OCR subsystem for your device. You will also have to record swipe events for replay. Currently, two devices are configured: the LG Nexus 5 and the OnePlus One (corresponding to the phones I have tested this on). Patches are welcome to add more phones.

To configure the OCR system, you should add an entry in `ocr/devices.py` corresponding to your device. The model name can be obtained by simply running `android_assistant.py` while connected to the device (it should error out with the expected model name). Essentially, you will need to take a screenshot of the game and derive the position of the "upcoming tile" pane, as well as the position and spacing of the tile grid. (This part could probably use more automation and/or simplification!)

To record events, simply run `python -m android.inputemu --record up down left right` and execute the appropriate gesture on your phone when prompted.

## Manual assistant
The manual assistant is a general-purpose Threes! assistant that works with any implementation of Threes!. You tell it the board and upcoming tile set, and the assistant calculates the best move.

### Running
Run `manual_assistant.py` to start the manual assistant.

Note that the manual assistant expects to see sequential moves. If you skip ahead (making moves without the assistant), quit the assistant by pressing Ctrl+C and start it again. Otherwise, you might receive an error message like "impossible situation" if you enter a board that is not sequential to the previous board.

### Entering boards

When entering the next board, you can use spaces, newlines and/or commas to separate tiles. Read from left to right, then top to bottom. Enter a zero for empty spaces. Example input:

- Using commas and newlines:


        96,2,3,0
        2,1,1,0
        2,1,0,0
        0,0,2,0
- Using commas alone:


        96,2,3,0,2,1,1,0,2,1,0,0,0,0,2,0
- Using spaces:


        96 2 3 0
        2 1 1 0
        2 1 0 0
        0 0 2 0

You can also input a "delta" from the previous board. Specify row or column in which the new tile spawned, and the value of the tile that spawned (you can omit this if there was only one possible new tile last move, e.g. if it was red or blue). Also specify the move you made if it wasn't the move suggested by the AI.

Columns and rows are numbered left-to-right and top-to-bottom: column 1 is the left column and row 1 is the top row.

For example, if the board is swiped up, and goes from

    96 2 3 0
    2 1 1 0
    2 1 0 0
    0 0 2 0

to

    96 3 3 0
    2 1 1 0
    2 0 2 0
    0 3 0 0

then you'd send `2,3,up` as the board (in the 2nd column, a 3 spawned). If the AI had recommended the `up` move then you could simply omit that and send `2,3`. If the upcoming tile had been forecast as 3, you could omit the 3 and send just `2`.

By entering deltas, you will save yourself a lot of time. In most cases, you only need to enter one number (the column/row that changed).

### Entering tiles
When entering the upcoming tile, use one of the following formats:

- a color: `blue` (1), `red` (2) or `white` (3+)
- a number group: `1`, `2`, `3`, `3+`, `6+`, or e.g. `24,48,96`, `24 48 96`
    - `3+` means it could be a 3 or higher; use this with older Threes! that don't show a "plus" sign on bonus tiles
    - `6+` means it is any bonus tile; use this if the upcoming tile is "+"
    - `24,48,96` means it is one of those three; use this with newer Threes! that show you explicit options for the bonus tile value.
