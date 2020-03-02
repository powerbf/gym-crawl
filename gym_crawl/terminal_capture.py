# -*- coding: utf-8 -*-
"""Module for capturing terminal output, including handling ASCII escape sequences
"""

from curses import ascii
import re
import sys

ESC = chr(ascii.ESC)
DEL = chr(ascii.DEL)

CLEAR_SCREEN = '[2J'
ESC_CLEAR_SCREEN = ESC + CLEAR_SCREEN


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
        self.screen_cols = cols
        self.screen_rows = rows
        self.data = None
        self.frame = None
        self.row = 0
        self.col = 0
        self.saved_row = None
        self.saved_col = None
        self._init_frame()

    def to_string(self):
        # return screen contents as string
        string = ''
        for row in self.frame:
            string += ''.join(row)
            string += '\n'
        return string

    def render(self, row, col):
        """ print screen contents
            by default, prints at current cursor. or at row, col if both are specified (1-based, not 0-based)
        """
        if row is not None and col is not None:
            sys.stdout.write(ESC + '[' + str(row) + ';' + str(col) + 'H')
        sys.stdout.write(self.to_string())
        sys.stdout.flush()

    def handle_output(self, data):
        # update our internal representation of the screen
        # this is tricky because the raw data contains ASCII control sequences
        print('\nProcessing data: ' + make_printable(data), file=sys.stderr)
        self.data = data
        i = 0
        while i < len(data):
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
            elif data[i] >= ' ' and data[i] != DEL:
                #print('Setting character at {},{}\n'.format(self.row, self.col), file=sys.stderr)
                self.frame[self.row][self.col] = data[i]
                self.col += 1

            i += 1

    def _handle_escape_sequence(self, esc_seq):
        #print('Handling escape sequence: ' + make_printable(esc_seq), file=sys.stderr)
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
                # cursor up and to start of line
                self.col = 0
                self.row -= self._extract_number(esc_seq, 1)
                if self.row < 0:
                    self.row = 0
            elif esc_seq[-1] == 'F':
                # cursor down and to start of line
                self.col = 0
                self.row += self._extract_number(esc_seq, 1)
                if self.row > self.screen_rows - 1:
                    self.row = self.screen_rows - 1
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
                    #print('Moved cursor to {},{}\n'.format(self.row, self.col), file=sys.stderr)
                else:
                    self.row = 0
                    self.col = 0
            elif esc_seq == CLEAR_SCREEN:
                # clear screen
                self._clear_frame()
            elif esc_seq == '[0K' or esc_seq == '[K':
                # clear from cursor to end of line
                for j in range(self.col, self.screen_cols):
                    self.frame[self.row][j] = ' '
            elif esc_seq == '[1K':
                # clear from cursor to beginning of line
                for j in range(0, self.col):
                    self.frame[self.row][j] = ' '
            elif esc_seq == '[2K':
                # clear whole line
                for j in range(self.screen_cols):
                    self.frame[self.row][j] = ' '
            elif esc_seq[-1] =='M':
                # delete lines
                num = self._extract_number(esc_seq, 1)
                for dest in range(self.row, self.screen_rows):
                    src = dest + num
                    if src < self.screen_rows:
                        self.frame[dest] = self.frame[src]
                    else:
                        self.frame[dest] = [' '] * self.screen_cols
            elif esc_seq[-1] == 'P':
                # CSI Ps P  Delete Ps Character(s) (default = 1) (DCH).
                num = self._extract_number(esc_seq, 1)
                line = self.frame[self.row]
                for dest in range(self.col, self.screen_cols):
                    src = dest + num
                    if src < self.screen_cols:
                        line[dest] = line[src]
                    else:
                        line[dest] = ' '
            elif esc_seq[-1] == 'X':
                # CSI Ps X  Erase Ps Character(s) (default = 1) (ECH).
                num = self._extract_number(esc_seq, 1)
                line = self.frame[self.row]
                for dest in range(self.col-num, self.screen_cols):
                    src = dest + num
                    if src < self.screen_cols:
                        line[dest] = line[src]
                    else:
                        line[dest] = ' '
            elif esc_seq[-1] == 'd':
                # set vertical position
                self.row = self._extract_number(esc_seq, 1) - 1
            elif esc_seq[-1] == 'm':
                # TODO: font effects
                pass
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
                print('Unknown escape sequence: ESC' + esc_seq, file=sys.stderr)
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
            print('Unknown escape sequence: ESC' + esc_seq, file=sys.stderr)

    def _extract_number(self, string, default):
        m = re.search(r'(\d+)', string)
        if m and m.group(1) != '':
            return int(m.group(1))
        else:
            return default

    def _init_frame(self):
        self.frame = []
        for row in range(self.screen_rows):
            self.frame.append([' '] * self.screen_cols)
        self.row = 0
        self.col = 0
        self.frame_count = 0

    def _clear_frame(self):
        for row in range(self.screen_rows):
            for col in range(self.screen_cols):
                self.frame[row][col] = ' '
        self.row = 0
        self.col = 0


