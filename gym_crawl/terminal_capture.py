# -*- coding: utf-8 -*-
"""Module for capturing terminal output, including handling ASCII escape sequences
"""

from curses import ascii
import re
import sys
import logging

logger = logging.getLogger('term-capture')

ESC = chr(ascii.ESC)
DEL = chr(ascii.DEL)

CLEAR_SCREEN = '[2J'
ESC_CLEAR_SCREEN = ESC + CLEAR_SCREEN
ESC_GOTO_NEXT_LINE = ESC + '[E'

ESC_FONT_NORMAL = ESC + '[0m'

DEFAULT_FOREGROUND_COLOR = 39

# background colors
BG_COLOR_BLACK = 40
BG_COLOR_RED = 41
BG_COLOR_GREEN = 42
BG_COLOR_YELLOW = 43
BG_COLOR_BLUE = 44
BG_COLOR_MAGENTA = 45
BG_COLOR_CYAN = 46
BG_COLOR_WHITE = 47
BG_COLOR_DEFAULT = 49
BG_COLOR_BRIGHT_BLACK = 100
BG_COLOR_BRIGHT_RED = 101
BG_COLOR_BRIGHT_GREEN = 102
BG_COLOR_BRIGHT_YELLOW = 103
BG_COLOR_BRIGHT_BLUE = 104
BG_COLOR_BRIGHT_MAGENTA = 104
BG_COLOR_BRIGHT_CYAN = 106
BG_COLOR_BRIGHT_WHITE = 107

def make_printable(string):
    """ Replace non-printable characters with codes
    """
    result = ''
    for ch in string:
        if ch >= ' ' and ch <= '~':
            result += ch
        elif ch == ESC:
            result += '\ESC'
        elif ch == DEL:
            result += 'DEL'
        else:
            o = ord(ch)
            result += "\\x%0.2x" % o
    return result


class TerminalCapture:

    def __init__(self, rows = 24, cols = 80):
        logger.debug('__init__')
        self.screen_cols = cols
        self.screen_rows = rows
        self.data = None
        self.screen = None
        self.row = 0
        self.col = 0
        self.saved_row = None
        self.saved_col = None
        self.curr_foreground_color = DEFAULT_FOREGROUND_COLOR
        self.curr_background_color = BG_COLOR_BLACK
        self.bold = False
        self._init_screen()


    def to_string(self):
        # return screen contents as string
        string = ''
        for line in self.screen:
            for char in line:
                string += char['char']
            string += '\n'
        return string

    def render(self, row, col, show_border = True):
        """ print screen contents
            by default, prints at current cursor. or at row, col if both are specified (1-based, not 0-based)
        """
        if row is not None and col is not None:
            sys.stdout.write(ESC + '[' + str(row) + ';' + str(col) + 'H')
        sys.stdout.write(ESC_FONT_NORMAL) # reset to defaults

        if show_border:
            sys.stdout.write('/')
            for i in range(self.screen_cols):
                sys.stdout.write('-')
            sys.stdout.write('\\' + ESC_GOTO_NEXT_LINE)

        last_fg_color = None
        last_bg_color = None
        last_bold = False

        for line in self.screen:
            if show_border:
                sys.stdout.write('|')

            for char in line:

                # set bold
                bold = char['bold']
                if bold != last_bold:
                    if bold:
                        sys.stdout.write(ESC + '[1m')
                    else:
                       sys.stdout.write(ESC_FONT_NORMAL)
                       last_fg_color = None
                       last_bg_color = None
                    last_bold = bold
 
                # set foreground color
                fg_color = char['foreground_color']
                if fg_color != last_fg_color:
                    sys.stdout.write(ESC + '[' + str(fg_color) + 'm')
                    last_fg_color = fg_color

                # set background color
                bg_color = char['background_color']
                if bg_color != last_bg_color:
                    sys.stdout.write(ESC + '[' + str(bg_color) + 'm')
                    last_bg_color = bg_color

                sys.stdout.write(char['char'])

            if show_border:
                sys.stdout.write(ESC_FONT_NORMAL)
                last_fg_color = None
                last_bg_color = None
                last_bold = False
                sys.stdout.write('|')

            sys.stdout.write(ESC_GOTO_NEXT_LINE)

        if show_border:
            sys.stdout.write('\\')
            for i in range(self.screen_cols):
                sys.stdout.write('-')
            sys.stdout.write('/' + ESC_GOTO_NEXT_LINE)

        sys.stdout.flush()

    def handle_output(self, data):
        # update our internal representation of the screen
        # this is tricky because the raw data contains ASCII control sequences
        logger.debug('\nProcessing data: ' + make_printable(data))
        self.data = data
        i = 0
        string = ''
        string_row = 0
        string_col = 0
        while i < len(data):
            if data[i] >= ' ' and data[i] != DEL:
                if logger.isEnabledFor(logging.DEBUG):
                    if string == '':
                        string_row = self.row
                        string_col = self.col
                    string += data[i]
                self.screen[self.row][self.col]['char'] = data[i]
                self.screen[self.row][self.col]['foreground_color'] = self.curr_foreground_color
                self.screen[self.row][self.col]['background_color'] = self.curr_background_color
                self.screen[self.row][self.col]['bold'] = self.bold
                self.col += 1
            else:
                if logger.isEnabledFor(logging.DEBUG) and len(string) > 0:
                    logger.debug('Placed string at {:d},{:d}: {}'.format(string_row, string_col, string))
                    string = ''
            
                if data[i] == ESC:
                    if i == len(data) - 1:
                        # ESC is the last char
                        break

                    # extract the escape sequence
                    j = i + 1
                    if data[j] == '[' or data[j] == '(':
                        j += 1
                        while j < len(data) - 1 and (data[j] < '\x40' or data[j] > '\x7e'):
                            j += 1
                    esc_seq = data[i:j+1]
                    i = j

                    # now handle the escape sequence
                    self._handle_escape_sequence(esc_seq)
     
                elif data[i] == '\n':
                    self.row += 1
                    self.col = 0
                elif data[i] == '\r':
                    self.col = 0

            i += 1

    def _handle_escape_sequence(self, esc_seq):
        logger.debug('Handling escape sequence: ' + make_printable(esc_seq))
        esc_seq = esc_seq[1:] # discard ESC character
        if esc_seq == '':
            pass
        elif esc_seq[0] == '(' or esc_seq[0] == ')':
            # selecting character set
            pass
        elif esc_seq[0] == '[':
            if esc_seq[-1] == 'A':
                # cursor up
                self.row -= self._extract_number(esc_seq, 1)
                if self.row < 0:
                    self.row = 0
            elif esc_seq[-1] == 'B':
                # cursor down
                self.row += self._extract_number(esc_seq, 1)
                if self.row > self.screen_rows - 1:
                    self.row = self.screen_rows - 1
            elif esc_seq[-1] == 'C':
                # cursor forward
                self.col += self._extract_number(esc_seq, 1)
                if self.col > self.screen_cols - 1:
                    self.col = self.screen_cols - 1
            elif esc_seq[-1] == 'D':
                # cursor back
                self.col -= self._extract_number(esc_seq, 1)
                if self.col < 0:
                    self.col = 0
            if esc_seq[-1] == 'E':
                # CNL (Cursor Next Line): go to start of nth line down
                self.col = 0
                self.row += self._extract_number(esc_seq, 1)
                if self.row > self.screen_rows - 1:
                    self.row = self.screen_rows - 1
            elif esc_seq[-1] == 'F':
                # CPL (Cursor Previous Line): go to start of nth line up
                self.col = 0
                self.row -= self._extract_number(esc_seq, 1)
                if self.row < 0:
                    self.row = 0
            elif esc_seq[-1] == 'G':
                # move cursor to specified column
                # convert from 1-based to 0-based
                self.col = self._extract_number(esc_seq, 1) - 1
            elif esc_seq[-1] == 'H' or esc_seq[-1] == 'f':
                # move to specified cursor to position
                m = re.search(r'(\d*);(\d*)', esc_seq)
                if m :
                    # coords are 1-based, so we have to subtract one to convert to 0-based
                    self.row = 0 if m.group(1) == '' else int(m.group(1))-1
                    self.col = 0 if m.group(2) == '' else int(m.group(2))-1
                else:
                    self.row = 0
                    self.col = 0
                logger.debug('Moved cursor to {},{}'.format(self.row, self.col))
            elif esc_seq == CLEAR_SCREEN:
                # clear screen
                self._clear_screen()
            elif esc_seq == '[0K' or esc_seq == '[K':
                # clear from cursor to end of line
                for j in range(self.col, self.screen_cols):
                    self.screen[self.row][j] = self._new_char()
            elif esc_seq == '[1K':
                # clear from cursor to beginning of line
                for j in range(0, self.col):
                    self.screen[self.row][j] = self._new_char()
            elif esc_seq == '[2K':
                # clear whole line
                for j in range(self.screen_cols):
                    self.screen[self.row][j] = self._new_char()
            elif esc_seq[-1] =='M':
                # delete lines
                num = self._extract_number(esc_seq, 1)
                for dest in range(self.row, self.screen_rows):
                    src = dest + num
                    if src < self.screen_rows:
                        self.screen[dest] = self.screen[src]
                    else:
                        self.screen[dest] = self._new_line()
            elif esc_seq[-1] == 'P':
                # CSI Ps P  Delete Ps Character(s) (default = 1) (DCH).
                num = self._extract_number(esc_seq, 1)
                line = self.screen[self.row]
                for dest in range(self.col, self.screen_cols):
                    src = dest + num
                    if src < self.screen_cols:
                        line[dest] = line[src]
                    else:
                        line[dest] = self._new_char()
            elif esc_seq[-1] == 'X':
                # CSI Ps X  Erase Ps Character(s) (default = 1) (ECH).
                num = self._extract_number(esc_seq, 1)
                logger.debug('Erasing {} chars at {},{}'.format(num, self.row, self.col))
                line = self.screen[self.row]
                for dest in range(self.col, min(self.col+num, self.screen_cols)):
                    line[dest] = self._new_char()
                self.col = min(self.col+num, self.screen_cols-1)
            elif esc_seq[-1] == 'd':
                # set vertical position
                self.row = self._extract_number(esc_seq, 1) - 1
            elif esc_seq[-1] == 'm':
                # font effects
                nums = self._extract_numbers(esc_seq, 0)
                for num in nums:
                    if num == 0:
                        # reset everything
                        self.curr_foreground_color = DEFAULT_FOREGROUND_COLOR
                        self.curr_background_color = BG_COLOR_BLACK
                        logger.debug('Set foreground color to: {}'.format(self.curr_foreground_color))
                        self.bold = False
                    elif num == 1:
                        self.bold = True
                    elif num == DEFAULT_FOREGROUND_COLOR or (num >= 30 and num <= 37) or (num >= 90 and num <=97):
                        self.curr_foreground_color = num 
                        logger.debug('Set foreground color to: {}'.format(self.curr_foreground_color))
                    elif num == BG_COLOR_DEFAULT:
                        self.curr_background_color = BG_COLOR_BLACK
                    elif num >= BG_COLOR_BLACK and num <= BG_COLOR_WHITE:
                        self.curr_background_color = num 
                    elif num >= BG_COLOR_BRIGHT_BLACK and num <= BG_COLOR_BRIGHT_WHITE:
                        self.curr_background_color = num 
            elif esc_seq[-1] == 'r':
                # TODO: set scroll region
                pass
            elif esc_seq[-1] == 'h':
                # Set mode
                if esc_seq == '[4h':
                    # Insert Mode (IRM)
                    pass
            elif esc_seq[-1] == 'l':
                # Reset mode (inverse of control codes ending in h)
                if esc_seq == '[4l':
                    # Replace Mode (IRM)
                    pass
            elif esc_seq[-1] == 't':
                # Xterm window settings
                pass
            else:
                logger.debug('Unknown escape sequence: ESC' + esc_seq)
        elif esc_seq == '7':
            # save cursor position
            self.saved_row = self.row
            self.saved_col = self.col
        elif esc_seq == '8':
            # restore cursor position
            if self.saved_row is not None and self.saved_col is not None:
                self.row = self.saved_row
                self.col = self.saved_col
        elif esc_seq == 'M':
            # Moves cursor up one line in same column. If cursor is at top margin, screen performs a scroll-down.
            if self.row != 0:
                self.row -= 1
        elif esc_seq == 'D':
            # Moves cursor up down line in same column. If cursor is at bottom margin, screen performs a scroll-up.
            if self.row < self.screen_rows - 1:
                self.row += 1
        elif esc_seq == 'E':
            # Moves cursor to first position on next line. If cursor is at bottom margin, screen performs a scroll-up.
            if self.row < self.screen_rows - 1:
                self.row += 1
            self.col = 0
        elif esc_seq == '=':
            # Enter alternate keypad mode (numlock off?)
            pass
        elif esc_seq == '>':
            # Exit alternate keypad mode (numlock on?)
            pass
        else:
            logger.debug('Unknown escape sequence: ESC' + esc_seq)

    def _extract_number(self, string, default):
        m = re.search(r'(\d+)', string)
        if m and m.group(1) != '':
            return int(m.group(1))
        else:
            return default

    def _extract_numbers(self, string, default=None):
        strings = re.findall(r'(\d+)', string)
        results = []
        for string in strings:
            results.append(int(string))
        if len(results) == 0 and default != None:
            results.append(default)
        return results

    def _init_screen(self):
        self.screen = []
        for row in range(self.screen_rows):
            self.screen.append(self._new_line())
        self.row = 0
        self.col = 0

    def _clear_screen(self):
        for row in range(self.screen_rows):
            for col in range(self.screen_cols):
                self.screen[row][col] = self._new_char()
        self.row = 0
        self.col = 0

    def _new_char(self):
        char = {}
        char['char'] = ' '
        char['foreground_color'] = DEFAULT_FOREGROUND_COLOR
        char['background_color'] = BG_COLOR_BLACK
        char['bold'] = False
        return char

    def _new_line(self):
        line = []
        for col in range(self.screen_cols):
            line.append(self._new_char())
        return line

