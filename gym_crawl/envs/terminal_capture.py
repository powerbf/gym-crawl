from curses import ascii
import re
import sys

class TerminalCapture:

    def __init__(self, rows = 24, cols = 80):
        self.SCREEN_COLS = cols
        self.SCREEN_ROWS = rows
        self.data = None
        self.frame = None
        self.row = 0
        self.col = 0
        self._init_frame()

    def to_string(self):
        # return screen contents as string
        string = ''
        for row in self.frame:
            string += ''.join(row)
            string += '\n'
        return string

    def handle_output(self, data):
        # update our internal representation of the screen
        # this is tricky because the raw data contains ASCII control sequences
        print('\nProcessing data: ' + re.sub(r'\x1b', 'ESC', data), file=sys.stderr)
        self.data = data
        i = 0
        while i < len(data):
            if data[i] == '\x1b':
                if i == len(data) - 1:
                    # ESC is the last char
                    break

                # extract the escape sequence
                j = i + 1
                if data[j] == '[' or data[j] == '(':
                    j += 1 
                    while j < len(data) - 1 and (data[j] < '\x40' or data[j] > '\x7e'):
                        j += 1
                esc_seq = data[i+1:j+1] # excludes ESC character
                i = j

                # now handle the escape sequence
                self._handle_escape_sequence(esc_seq)
 
            elif data[i] == '\n':
                self.row += 1
                self.col = 0
            elif data[i] == '\r':
                self.col = 0
            elif data[i] >= ' ' and data[i] != '\07f':
                #print('Setting character at {},{}\n'.format(self.row, self.col), file=sys.stderr)
                self.frame[self.row][self.col] = data[i]
                self.col += 1

            i += 1

    def _handle_escape_sequence(self, esc_seq):
        print('Handling escape sequence: ESC' + esc_seq, file=sys.stderr)
        if esc_seq[0] == '[':
            if esc_seq[-1] == 'A':
                # cursor up
                self.row -= self._extract_number(esc_seq, 1)
                if self.row < 0:
                    self.row = 0
            elif esc_seq[-1] == 'B':
                # cursor down
                self.row += self._extract_number(esc_seq, 1)
                if self.row > self.SCREEN_ROWS - 1:
                    self.row = self.SCREEN_ROWS - 1
            elif esc_seq[-1] == 'C':
                # cursor forward
                self.col += self._extract_number(esc_seq, 1)
                if self.col > self.SCREEN_COLS - 1:
                    self.col = self.SCREEN_COLS - 1
            elif esc_seq[-1] == 'D':
                # cursor back
                self.col -= self._extract_number(esc_seq, 1)
                if self.col < 0:
                    self.col = 0
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
            elif esc_seq == '[2J':
                # clear screen
                self._clear_frame()
            elif esc_seq == '[0K' or esc_seq == '[K':
                # clear from cursor to end of line
                for j in range(self.col, self.SCREEN_COLS):
                    self.frame[self.row][j] = ' '
            elif esc_seq == '[1K':
                # clear from cursor to beginning of line
                for j in range(0, self.col):
                    self.frame[self.row][j] = ' '
            elif esc_seq == '[2K':
                # clear whole line
                for j in range(self.SCREEN_COLS):
                    self.frame[self.row][j] = ' '
            elif esc_seq[-1] =='M':
                # delete lines
                num = self._extract_number(esc_seq, 1)
                for dest in range(self.row, self.SCREEN_ROWS):
                    src = dest + num
                    if src < self.SCREEN_ROWS:
                        self.frame[dest] = self.frame[src]
                    else:
                        self.frame[dest] = [' '] * self.SCREEN_COLS           
            elif esc_seq[-1] == 'd':
                # set vertical position
                self.row = self._extract_number(esc_seq, 1) - 1
                #print('Set vertical position to {}'.format(self.row), file=sys.stderr)
        elif esc_seq == '7':
            #TODO: save cursor pos
            pass
        elif esc_seq == '8':
            #TODO: restore cursor pos
            pass
        elif esc_seq == 'M':
            # Moves cursor up one line in same column. If cursor is at top margin, screen performs a scroll-down.
            if self.row != 0:
                self.row -= 1
        elif esc_seq == 'D':
            # Moves cursor up down line in same column. If cursor is at bottom margin, screen performs a scroll-up.
            if self.row < self.SCREEN_ROWS - 1:
                self.row += 1
        elif esc_seq == 'E':
            # Moves cursor to first position on next line. If cursor is at bottom margin, screen performs a scroll-up.
            if self.row < self.SCREEN_ROWS - 1:
                self.row += 1
            self.col = 0

    def _extract_number(self, string, default):
        m = re.search(r'(\d+)', string)
        if m and m.group(1) != '':
            return int(m.group(1))
        else:
            return default

    def _init_frame(self):
        self.frame = []
        for row in range(self.SCREEN_ROWS):
            self.frame.append([' '] * self.SCREEN_COLS)
        self.row = 0
        self.col = 0
        self.frame_count = 0

    def _clear_frame(self):
        for row in range(self.SCREEN_ROWS):
            for col in range(self.SCREEN_COLS):
                self.frame[row][col] = ' '
        self.row = 0
        self.col = 0

