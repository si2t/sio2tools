# ! thanks to https://mike42.me/blog/2018-06-make-better-cli-progress-bars-with-unicode-block-characters for source codce
# code is slightly modified for my needs :p

import colorama
import math
import shutil
import sys
import time
from colorama import Fore

colorama.init(autoreset=True)

from typing import TextIO

TICK = f"{Fore.GREEN}✔{Fore.WHITE}"
XMARK = f"{Fore.RED}✘{Fore.WHITE}"
MAX_LAST_UPDATES = 200


def int_to_time(seconds: int):
    minutes, seconds = divmod(seconds, 60)
    minutes, seconds = round(minutes), round(seconds)
    return f"{minutes:02}:{seconds:02}"


class ProgressBar(object):
    def __init__(
        self,
        /,
        max_value,
        color="WHITE",
        target: TextIO = sys.stdout,
        length=40,
        additional_text="",
        remove_exit=False,
    ):
        self._target = target
        self._text_only = not self._target.isatty()
        self._width = length
        self._max = max_value
        self._color = getattr(colorama.Fore, color.upper())
        self._text = additional_text
        self._remove_on_exit = remove_exit
        self._current = 0
        self._start = time.time()
        self._last_updates = []
        self._next_queue = []
        self._queue_free = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Set to 100% for neatness, if no exception is thrown
            self.update(1.0)
        if not self._text_only:
            if self._remove_on_exit:
                self._target.write(" " * (shutil.get_terminal_size()[0]))
            self._target.write("\n")
        self._target.flush()

    @property
    def current_progress(self):
        return self._current / self._max

    def update(self, progress: float, /, with_message: str = None):
        if len(self._last_updates) == 0:
            self._last_updates.append(time.time() - self._start)
        else:
            self._last_updates.append(
                time.time() - sum(self._last_updates) - self._start
            )
        while len(self._last_updates) > MAX_LAST_UPDATES:
            self._last_updates.pop(0)

        # print("\n", self._last_updates)
        avg = sum(self._last_updates) / len(self._last_updates)
        elapsed = int_to_time(time.time() - self._start)
        remaining = int_to_time((self._max - self._current + 1) * avg)

        # Progress bar itself
        if self._width < 12:
            # No label in excessively small terminal
            percent_str = ""
            progress_bar_str = ProgressBar.progress_bar_str(
                progress, self._width - 2, self._color
            )
        elif self._width < 40:
            # No padding at smaller size
            percent_str = " {:6.2f} %".format(progress * 100)
            progress_bar_str = (
                ProgressBar.progress_bar_str(progress, self._width - 11) + " ",
                self._color,
            )
        else:
            # Standard progress bar with padding and label
            percent_str = (
                " {:6.2f}% {} [{}>{}]".format(
                    progress * 100, self._text, elapsed, remaining
                )
                + "  "
            )
            progress_bar_str = " " * 5 + ProgressBar.progress_bar_str(
                progress, self._width - 21, self._color
            )
        # Write output
        if self._text_only:
            if with_message:
                self._target.write(with_message + "\n")
            self._target.write(progress_bar_str + percent_str + "\n")
            self._target.flush()
        else:
            if with_message:
                self._target.write(
                    "\033[G"
                    + with_message
                    + " " * (shutil.get_terminal_size()[0] - len(with_message) - 5)
                    + "\n"
                    + progress_bar_str
                    + percent_str
                )
            self._target.write("\033[G" + progress_bar_str + percent_str)
            self._target.flush()

    def update_next(self, with_message: str = None):
        self._next_queue.append(with_message)
        # invoke update if there is no update in progress
        self._invoke_queue()

    def _invoke_queue(self):
        if not self._queue_free:
            return

        self._queue_free = False
        while self._next_queue:
            self._current += 1
            self.update(self._current / self._max, with_message=self._next_queue.pop(0))
        self._queue_free = True

    @staticmethod
    def progress_bar_str(progress: float, width: int, color: Fore):
        # 0 <= progress <= 1
        progress = min(1, max(0, progress))
        whole_width = math.floor(progress * width)
        remainder_width = (progress * width) % 1
        part_width = math.floor(remainder_width * 8)
        ascii_progress = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]
        part_char = ascii_progress[part_width]
        if (width - whole_width - 1) < 0:
            part_char = ""
        line = (
            color
            + colorama.Back.LIGHTBLACK_EX
            + "█" * whole_width
            + part_char
            + " " * (width - whole_width - 1)
            + colorama.Style.RESET_ALL
        )
        return line
