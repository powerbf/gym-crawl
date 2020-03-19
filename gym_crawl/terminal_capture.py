# -*- coding: utf-8 -*-
"""Module for capturing terminal output, including handling ASCII escape sequences
"""

import re
import logging

from gym_crawl.chars import make_printable, ESC, BS, DEL
from gym_crawl.terminal import *

logger = logging.getLogger('term-capture')


CLEAR_SCREEN = ESC_CLEAR_SCREEN[1:]



class TerminalCapture:

    def __init__(self, rows = 24, cols = 80):
        logger.debug('__init__')
        self.data = None
        self.screen = Screen(rows, cols)
        self.row = 0
        self.col = 0
        self.saved_row = None
        self.saved_col = None
        self.curr_foreground_color = FG_COLOR_DEFAULT
        self.curr_background_color = BG_COLOR_BLACK
        self.bold = False
        self.line_wrap = False
        self.scroll_region_start = 0
        self.scroll_region_end = self.screen.rows - 1

    def handle_output(self, data):
        # update our internal representation of the screen
        # this is tricky because the raw data contains ASCII control sequences
        logger.debug('Processing data:\n' + make_printable(data, 80))
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
                cell = self.screen.get(self.row, self.col)
                cell.glyph = data[i]
                cell.fg_color = self.curr_foreground_color
                cell.bg_color = self.curr_background_color
                cell.bold = self.bold
                # move cursor on
                if self.col == self.screen.cols - 1:
                    if self.line_wrap:
                        self._set_pos(self.row + 1, 0)
                else:
                    self._set_col(self.col + 1)
            else:
                if logger.isEnabledFor(logging.DEBUG) and len(string) > 0:
                    logger.debug('Printed "{}" at {:d},{:d}. Cursor now at {:d},{:d}'.format(
                        string, string_row+1, string_col+1, self.row+1, self.col+1))
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
                    # Moves cursor down one line in same column. If cursor is at bottom margin, screen performs a scroll-up.
                    if self.row < self.scroll_region_end:
                        self.row += 1
                    else:
                        for row in range(self.scroll_region_start, self.scroll_region_end):
                            self.screen.cells[row] = self.screen.cells[row+1]
                        self.screen.cells[self.scroll_region_end] = self._new_line()
                        logger.debug('LF: Scrolled up region {:d},{:d}'.format(self.scroll_region_start+1, self.scroll_region_end+1))
                    logger.debug('LF: Cursor now at {:d},{:d}'.format(self.row+1, self.col+1))
                elif data[i] == '\r':
                    self._set_col(0)
                    logger.debug('CR: Cursor moved to {:d},{:d}'.format(self.row+1, self.col+1))
                elif data[i] == BS:
                    # backspace just moves the cursor left
                    self._set_col(self.col - 1)
                    logger.debug('BS: Cursor moved to {:d},{:d}'.format(self.row+1, self.col+1))
                else:
                    logger.warn("Unhandled character: " + make_printable(data[i]))

            i += 1

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Screen:\n" + self.screen.to_string())

    def _handle_escape_sequence(self, esc_seq):
        old_row = self.row
        old_col = self.col
        esc_seq = esc_seq[1:] # discard ESC character
        if esc_seq == '':
            pass
        elif esc_seq[0] == '(' or esc_seq[0] == ')':
            # selecting character set
            logger.debug('ESC{}: Select character set (ignored)'.format(esc_seq))
            pass
        elif esc_seq[0] == '[':
            if esc_seq[-1] == 'A':
                # cursor up
                self._set_row(self.row - self._extract_number(esc_seq, 1))
            elif esc_seq[-1] == 'B':
                # cursor down
                self._set_row(self.row + self._extract_number(esc_seq, 1))
            elif esc_seq[-1] == 'C':
                # cursor forward
                self._set_col(self.col + self._extract_number(esc_seq, 1))
            elif esc_seq[-1] == 'D':
                # cursor back
                self._set_col(self.col - self._extract_number(esc_seq, 1))
            elif esc_seq[-1] == 'E':
                # CNL (Cursor Next Line): go to start of nth line down
                num = self._extract_number(esc_seq, 1)
                self._set_pos(self.row + num, 0)
            elif esc_seq[-1] == 'F':
                # CPL (Cursor Previous Line): go to start of nth line up
                num = self._extract_number(esc_seq, 1)
                self._set_pos(self.row - num, 0)
            elif esc_seq[-1] == 'G':
                # move cursor to specified column (1-based)
                num = self._extract_number(esc_seq, 1)
                self._set_col(num, 1)
            elif esc_seq[-1] == 'H' or esc_seq[-1] == 'f':
                # move to specified cursor to position
                m = re.search(r'(\d*);(\d*)', esc_seq)
                if m :
                    # coords are 1-based, so we have to subtract one to convert to 0-based
                    row = 0 if m.group(1) == '' else int(m.group(1))-1
                    col = 0 if m.group(2) == '' else int(m.group(2))-1
                else:
                    row = 0
                    col = 0
                self._set_pos(row, col)
            elif esc_seq == CLEAR_SCREEN:
                # clear screen
                self._clear_screen()
            elif esc_seq[-1] == 'K':
                # ESC[nK - Erase in line (EL) - erases without moving cursor
                start = None
                end = None
                if esc_seq == '[0K' or esc_seq == '[K':
                    # erase from cursor (inclusive) to end of line
                    start = self.col
                    end = self.screen.cols - 1
                elif esc_seq == '[1K':
                    # erase from cursor (inclusive) to beginning of line
                    start = 0
                    end = self.col
                elif esc_seq == '[2K':
                    # erase whole line
                    start = 0
                    end = self.screen.cols - 1
                    
                if start == None or end == None:
                    logger.warn('Unknown escape sequence: ESC' + esc_seq)
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug('ESC{}: Erasing from {:d},{:d} to {:d},{:d}'.format(make_printable(esc_seq), self.row+1, start+1, self.row+1, end+1))
                    
                    for j in range(start, end+1):
                        cell = self.screen.cells[self.row][j]
                        cell.glyph = ' '
                        cell.fg_color = self.curr_foreground_color
                        cell.bg_color = self.curr_background_color
                        cell.bold = self.bold
            elif esc_seq[-1] =='M':
                # delete lines
                num = self._extract_number(esc_seq, 1)
                logger.debug('Deleting {:d} lines'.format(num))
                for dest in range(self.row, self.screen.rows):
                    src = dest + num
                    if src < self.screen.rows:
                        self.screen.cells[dest] = self.screen.cells[src]
                    else:
                        self.screen.cells[dest] = self._new_line()
            elif esc_seq[-1] == 'P':
                # CSI Ps P  Delete Ps Character(s) (default = 1) (DCH).
                num = self._extract_number(esc_seq, 1)
                line = self.screen.cells[self.row]
                logger.debug('Deleting {} chars at {},{}'.format(num, self.row+1, self.col+1))
                for dest in range(self.col, self.screen.cols):
                    src = dest + num
                    if src < self.screen.cols:
                        line[dest] = line[src]
                    else:
                        line[dest] = Cell()
            elif esc_seq[-1] == 'X':
                # CSI Ps X  Erase Ps Character(s) (default = 1) (ECH).
                num = self._extract_number(esc_seq, 1)
                logger.debug('Erasing {} chars at {},{}'.format(num, self.row+1, self.col+1))
                line = self.screen.cells[self.row]
                for dest in range(self.col, min(self.col+num, self.screen.cols)):
                    line[dest].glyph = ' '
                self._set_col(self.col + num)
            elif esc_seq[-1] == 'd':
                # set vertical position
                row = self._extract_number(esc_seq, 1)
                self._set_row(row, 1)
            elif esc_seq[-1] == 'm':
                # font effects
                nums = self._extract_numbers(esc_seq, 0)
                for num in nums:
                    if num == 0:
                        # reset everything
                        self.curr_foreground_color = FG_COLOR_DEFAULT
                        self.curr_background_color = BG_COLOR_BLACK
                        self.bold = False
                    elif num == 1:
                        self.bold = True
                    elif num == FG_COLOR_DEFAULT or (num >= 30 and num <= 37) or (num >= 90 and num <=97):
                        self.curr_foreground_color = num 
                    elif num == BG_COLOR_DEFAULT:
                        self.curr_background_color = BG_COLOR_BLACK
                    elif num >= BG_COLOR_BLACK and num <= BG_COLOR_LIGHT_GRAY:
                        self.curr_background_color = num 
                    elif num >= BG_COLOR_DARK_GRAY and num <= BG_COLOR_WHITE:
                        self.curr_background_color = num 
            elif esc_seq[-1] == 'r':
                # set scroll region
                m = re.search(r'(\d*);(\d*)', esc_seq)
                if m :
                    # coords are 1-based, so we have to subtract one to convert to 0-based
                    self.scroll_region_start = 0 if m.group(1) == '' else int(m.group(1))-1
                    if self.scroll_region_start < 0:
                        self.scroll_region_start = 0
                    self.scroll_region_end = self.screen.rows-1 if m.group(2) == '' else int(m.group(2))-1
                    if self.scroll_region_end > self.screen.rows-1:
                        self.scroll_region_end = self.screen.rows-1
                else:
                    self.scroll_region_start = 0
                    self.scroll_region_end = self.screen.rows-1
                logger.debug('Set scroll region to {},{}'.format(self.scroll_region_start+1, self.scroll_region_end+1))
            elif esc_seq[-1] == 'h':
                # Set mode
                if esc_seq == '[4h':
                    # Insert Mode (IRM)
                    logger.debug('Insert mode (ignored)')
                    pass
                elif esc_seq == '[=7h':
                    logger.debug('Turning line wrap on')
                    self.line_wrap = True
            elif esc_seq[-1] == 'l':
                # Reset mode (inverse of control codes ending in h)
                if esc_seq == '[4l':
                    # Replace Mode (IRM)
                    logger.debug('Replace mode (ignored)')
                    pass
                elif esc_seq == '[=7l':
                    logger.debug('Turning line wrap off')
                    self.line_wrap = False
            elif esc_seq[-1] == 't':
                # Xterm window settings
                logger.debug('Xterm settings (ignored)')
                pass
            else:
                logger.warn('Unknown escape sequence: ESC' + esc_seq)
        elif esc_seq == '7':
            # save cursor position
            self.saved_row = self.row
            self.saved_col = self.col
            logger.debug('Saved cursor position {:d},{:d}'.format(self.row+1, self.col+1))
        elif esc_seq == '8':
            # restore cursor position
            if self.saved_row is not None and self.saved_col is not None:
                self.row = self.saved_row
                self.col = self.saved_col
                logger.debug('Restored cursor position {:d},{:d}'.format(self.row+1, self.col+1))
        elif esc_seq == 'M':
            # Moves cursor up one line in same column. If cursor is at top margin, screen performs a scroll-down.
            if self.row > self.scroll_region_start:
                self.row -= 1
            else:
                for row in range(self.scroll_region_end, self.scroll_region_start, -1):
                    self.screen.cells[row] = self.screen.cells[row-1]
                self.screen.cells[self.scroll_region_start] = self._new_line()
                logger.debug('Scrolled down region {:d},{:d}'.format(self.scroll_region_start+1, self.scroll_region_end+1))
        elif esc_seq == 'D':
            # Moves cursor down one line in same column. If cursor is at bottom margin, screen performs a scroll-up.
            if self.row < self.scroll_region_end:
                self.row += 1
            else:
                for row in range(self.scroll_region_start, self.scroll_region_end):
                    self.screen.cells[row] = self.screen.cells[row+1]
                self.screen.cells[self.scroll_region_end] = self._new_line()
                logger.debug('Scrolled up region {:d},{:d}'.format(self.scroll_region_start+1, self.scroll_region_end+1))
        elif esc_seq == 'E':
            # Moves cursor to first position on next line. If cursor is at bottom margin, screen performs a scroll-up.
            self.col = 0
            if self.row < self.scroll_region_end:
                self.row += 1
            else:
                for row in range(self.scroll_region_start, self.scroll_region_end):
                    self.screen.cells[row] = self.screen.cells[row+1]
                self.screen.cells[self.scroll_region_end] = self._new_line()
                logger.debug('Scrolled up region {:d},{:d}'.format(self.scroll_region_start+1, self.scroll_region_end+1))
        elif esc_seq == '=':
            # Enter alternate keypad mode (numlock off?)
            logger.debug('Turn numlock off (ignored)')
            pass
        elif esc_seq == '>':
            # Exit alternate keypad mode (numlock on?)
            logger.debug('Turn numlock on (ignored)')
            pass
        else:
            logger.warn('Unknown escape sequence: ESC' + esc_seq)

        if logger.isEnabledFor(logging.DEBUG):
            esc_seq = 'ESC' + make_printable(esc_seq)
            if self.row != old_row or self.col != old_col:
                logger.debug(esc_seq + ': Cursor moved to {:d},{:d}'.format(self.row+1, self.col+1))
            elif re.match(r'ESC\[.*m', esc_seq):
                logger.debug(esc_seq  + ': Font is now: fg={}, bg={}'.format(self.curr_foreground_color, self.curr_background_color) 
                             + (' bold' if self.bold else ''))
            elif esc_seq.startswith('ESC(') or esc_seq.startswith('ESC)'):
                pass
            else:
                logger.debug(esc_seq + ': handled')


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

    def _clear_screen(self):
        self.screen.clear()
        self.row = 0
        self.col = 0

    def _new_line(self):
        return [Cell() for _ in range(self.screen.cols)]

    def _set_row(self, val, base = 0):
        val -= base
        if val < 0:
            val = 0
        elif val > self.screen.rows - 1:
            val = self.screen.rows - 1
        self.row = val

    def _set_col(self, val, base = 0):
        val -= base
        if val < 0:
            val = 0
        elif val > self.screen.cols - 1:
            val = self.screen.cols - 1
        self.col = val

    def _set_pos(self, row, col, base = 0):
        self._set_row(row, base)
        self._set_col(col, base)

