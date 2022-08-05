"""
    Vortex Download Manager (VDM)

    Multi-connection internet download manager, based on "LibCurl", and "youtube_dl". Original project, FireDM, by Mahmoud Elshahat.
    :copyright: (c) 2022 by Sixline
    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU GPLv3, see LICENSE.md for more details.

    Module description:
        This is a command line / Terminal view, as a layer between user and controller
        it must inherit from IView and implement all its abstract methods, see view.py
        currently it runs in interactive mode and not suitable for automated jobs.

"""

import os
import sys
import shutil
from queue import Queue
from threading import Event
from collections import namedtuple

if not __package__:
    __package__ = 'vdm'

from vdm.view import IView
from vdm import utils
from vdm.utils import format_bytes, format_seconds
from vdm import config


def write(s, end=''):
    sys.stdout.write(s + end)
    sys.stdout.flush()


terminal_size = namedtuple('terminal_size', ('width', 'height'))


def get_terminal_size():
    """get terminal window size, return 2-tuple (width, height)"""
    try:
        size = shutil.get_terminal_size()
    except:
        # default fallback values
        size = (100, 20)
    return terminal_size(*size)


class CmdView(IView):
    """concrete class for terminal user interface"""

    def __init__(self, controller=None):
        self.controller = controller
        self.total_size = None
        self.progress = 0
        self.terminal_size = None
        self.printing_bar = Event()
        self.sdt_buffer = Queue()

        self.printing_bar.clear()

    def reserve_last_line(self):
        self.printing_bar.set()

        write("\0337")  # Save cursor position
        write(f"\033[0;{self.terminal_size.height - 1}r")  # Reserve the bottom line
        write("\0338")  # Restore the cursor position
        write("\033[1A")  # Move up one line

        self.printing_bar.clear()

    def release_last_line(self):
        self.printing_bar.set()

        write("\0337")  # Save cursor position
        write(f"\033[0;{self.terminal_size.height}r")  # Drop margin reservation
        write(f"\033[{self.terminal_size.height};0f")  # Move the cursor to the bottom line
        write("\033[0K")  # Clean that line
        write("\0338")

        self.printing_bar.clear()

    def run(self):
        """setup terminal for progress bar"""
        if config.operating_system == 'Windows':
            return

        utils.my_print = self.normal_print
        self.terminal_size = get_terminal_size()
        self.reserve_last_line()

    def quit(self):
        """reset terminal"""
        if config.operating_system == 'Windows':
            return

        self.release_last_line()
        utils.my_print = print

    def print_progress_bar(self, percent, suffix='', bar_length=20, fill='█'):
        """print progress bar to screen, percent is number between 0 and 100"""

        scale = bar_length / 100
        filled_length = int(percent * scale)
        bar = fill * filled_length + ' ' * (bar_length - filled_length)

        # get screen size
        terminal = get_terminal_size()

        line = f'\r {percent}% [{bar}] {suffix}'
        end_spaces = terminal.width - len(line)
        line += ' ' * end_spaces

        # truncate line 
        line = line[:terminal.width]

        if config.operating_system == 'Windows':
            write(line, end='\r')
            return

        # terminal size has changed
        if terminal != self.terminal_size:
            self.release_last_line()
            self.terminal_size = terminal
            self.reserve_last_line()

        self.print_onlast(line)

    def print_onlast(self, s):
        self.printing_bar.set()

        write("\0337")  # Save cursor position
        write(f"\033[{self.terminal_size.height};0f")  # Move cursor to the bottom margin
        write(s, end='\r')  # Write the data
        write("\0338")  # Restore cursor position

        self.printing_bar.clear()

    def normal_print(self, s, end='\n'):
        self.sdt_buffer.put(s)
        if self.printing_bar.is_set():
            return

        for _ in range(self.sdt_buffer.qsize()):
            write(self.sdt_buffer.get(), end=end)

    def update_view(self, total_size=None, **kwargs):
        """update view"""

        progress = kwargs.get('progress', 0)
        speed = kwargs.get('speed')
        eta = kwargs.get('eta')
        downloaded = kwargs.get('downloaded')
        if total_size:
            self.total_size = total_size

        # in terminal view, it will be only one download takes place in a time
        # since there is no updates coming from d_list items, it is easier to identify the currently downloading item
        # by checking progress
        if 0 < progress < 100 <= self.progress:
            self.progress = progress

        if progress > 0 and self.progress < 100:
            # print progress bar on screen

            suffix = f'{format_bytes(downloaded, sep="", percision=1)}'
            if self.total_size:
                suffix += f'/{format_bytes(self.total_size, sep="", percision=1)}'
            suffix += f" {format_bytes(speed, tail='/s', percision=1)}" if speed else ''
            suffix += f', {format_seconds(eta, percision=0, fullunit=True)}' if eta else ''

            try:
                self.print_progress_bar(progress, suffix=suffix, fill='=')
            except:
                if config.test_mode:
                    raise

            # to ignore repeated updates after 100%
            self.progress = progress

    def get_user_response(self, msg, options, **kwargs):
        """a mimic for a popup window in terminal, to get user response, 
        example: if msg =   "File with the same name already exists\n
                            /home/mahmoud/Downloads/7z1900.exe\n
                            Do you want to overwrite file? "

        and option = ['Overwrite', 'Cancel download']
        the resulting box will looks like:

        *******************************************
        * File with the same name already exists  *
        * /home/mahmoud/Downloads/7z1900.exe      *
        * Do you want to overwrite file?          *
        * --------------------------------------- *
        * Options:                                *
        *   1: Overwrite                          *
        *   2: Cancel download                    *
        *******************************************
        Select Option Number: 

        """
        # map options to numbers starting from 1
        options_map = {i + 1: x for i, x in enumerate(options)}

        # split message to list of lines
        msg_lines = msg.split('\n')

        # format options in lines example: "  1: Overwrite",  and "  2: Cancel download"  
        options_lines = [f'  {k}: {str(v)}' for k, v in options_map.items()]

        # get the width of longest line in msg body or options
        max_line_width = max(max([len(line) for line in msg_lines]), max([len(line) for line in options_lines]))

        # get current terminal window size (width)
        terminal_width = get_terminal_size()[0]

        # the overall width of resulting msg box including border ('*' stars in our case)
        box_width = min(max_line_width + 4, terminal_width)

        # build lines without border
        output_lines = []
        output_lines += msg_lines
        separator = '-' * (box_width - 4)
        output_lines.append(separator)
        output_lines.append("Options:")
        output_lines += options_lines

        # add stars and space padding for each line
        for i, line in enumerate(output_lines):
            allowable_line_width = box_width - 4

            # calculate the required space to fill the line
            delta = allowable_line_width - len(line) if allowable_line_width > len(line) else 0

            # add stars
            line = '* ' + line + ' ' * delta + ' *'

            output_lines[i] = line

        # create message string
        msg = '\n'.join(output_lines)
        msg = '\n' + '*' * box_width + '\n' + msg + '\n' + '*' * box_width
        msg += '\n Select Option Number: '

        while True:
            txt = input(msg)
            try:
                # get user selection
                # it will raise exception if user tries to input number not in options_map
                response = options_map[int(txt)]
                print()  # print empty line
                break  # exit while loop if user entered a valid selection
            except:
                print('\n invalid entry, try again.\n')

        return response
