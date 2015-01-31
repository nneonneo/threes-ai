# About

AI for the game Threes! by Sirvo LLC. You can get the game from here: http://asherv.com/threes/

Building this AI was the inspiration for my later [2048 AI](https://github.com/nneonneo/2048-ai), and some of the ideas from the 2048 AI have been backported to this AI as well.

While I have not formally benchmarked the performance of this AI (yet), I know that it has successfully attained the 6144 tile multiple times, which is the highest tile available in the game. (Higher tiles are possible but unlikely, due to heavy random effects).

# Algorithm

The algorithm for this AI is already essentially detailed in [this StackOverflow answer](http://stackoverflow.com/a/22498940/1204143) describing my 2048 AI. In essence, it implements a highly-optimized bruteforce search over the game tree (all possible moves, tile spawn values and tile values), using expectimax optimization to combine the results and find the "best" possible move.

This Threes AI is actually more sophisticated than the 2048 AI in a number of ways: most notably, it accounts for the "deck" of upcoming tiles (the well-documented process by which the random incoming tiles are selected), and it properly handles all the possible tile spawn locations based on the moves that are made. In short: this Threes AI correctly (to the best of my knowledge) emulates every detail of the Threes game as part of the expectimax optimization process.

# Playing the game

There are some web-based versions of Threes, but I wanted to make the AI play against the real app. So, I built an "assistant" program for Android devices, called `android_assistant.py`, which communicates with the phone over ADB and makes moves completely automatically. It requires only USB ADB permissions (standard developer access), and does not require rooting or any other modification of the device or app. It uses the standard Android `screencap` utility to obtain the (visible) game state, computes the optimal move, then uses the Linux input event subsystem to generate swipe events.

To use `android_assistant.py`, you will need to configure the OCR subsystem for your device. You will also have to record swipe events for replay. Currently, two devices are configured: the LG Nexus 5 and the OnePlus One (corresponding to the phones I have tested this on). Patches are welcome to add more phones.

To configure the OCR system, you should add an entry in `ocr/devices.py` corresponding to your device. The model name can be obtained by simply running `android_assistant.py` while connected to the device (it should error out with the expected model name). Essentially, you will need to take a screenshot of the game and derive the position of the "upcoming tile" pane, as well as the position and spacing of the tile grid. (This part could probably use more automation and/or simplification!)

To record events, simply run `android_inputemu.py --record up down left right` and execute the appropriate gesture on your phone when prompted.
