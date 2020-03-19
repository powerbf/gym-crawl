'''
Representation of ANSI terminal
'''
import sys
from gym_crawl.chars import ESC

# foreground colors
FG_COLOR_BLACK = 30
FG_COLOR_RED = 31
FG_COLOR_GREEN = 32
FG_COLOR_BROWN = 33 # supposedly normal intensity yellow
FG_COLOR_BLUE = 34
FG_COLOR_MAGENTA = 35
FG_COLOR_CYAN = 36
FG_COLOR_LIGHT_GRAY = 37 # normal intensity white
FG_COLOR_DEFAULT = 39
FG_COLOR_DARK_GRAY = 90 # aka bright black
FG_COLOR_LIGHT_RED = 91
FG_COLOR_LIGHT_GREEN = 92
FG_COLOR_YELLOW = 93 # aka bright yellow
FG_COLOR_LIGHT_BLUE = 94
FG_COLOR_LIGHT_MAGENTA = 95
FG_COLOR_LIGHT_CYAN = 96
FG_COLOR_WHITE = 97 # aka bright white

# background colors
BG_COLOR_BLACK = 40
BG_COLOR_RED = 41
BG_COLOR_GREEN = 42
BG_COLOR_BROWN = 43 # supposedly normal intensity yellow
BG_COLOR_BLUE = 44
BG_COLOR_MAGENTA = 45
BG_COLOR_CYAN = 46
BG_COLOR_LIGHT_GRAY = 47 # normal intensity white
BG_COLOR_DEFAULT = 49
BG_COLOR_DARK_GRAY = 100 # aka bright black
BG_COLOR_LIGHT_RED = 101
BG_COLOR_LIGHT_GREEN = 102
BG_COLOR_YELLOW = 103 # aka bright yellow
BG_COLOR_LIGHT_BLUE = 104
BG_COLOR_LIGHT_MAGENTA = 105
BG_COLOR_LIGHT_CYAN = 106
BG_COLOR_WHITE = 107 # aka bright white

# Escape sequences
ESC_CLEAR_SCREEN = ESC + '[2J'
ESC_FONT_NORMAL = ESC + '[0m'
ESC_GOTO_NEXT_LINE = ESC + '[E'


class Cell:
    """ Representation of a single location on the terminal screen"""
    
    def __init__(self):
        self.glyph = ' '
        self.fg_color = FG_COLOR_DEFAULT
        self.bg_color = BG_COLOR_BLACK
        self.bold = False


class Screen:
    """ Representation of the terminal screen """
    
    def __init__(self, rows = 24, cols = 80):
        self.rows = rows
        self.cols = cols
        self.cells = None
        self.clear()
        
    def clear(self):
        self.cells = []
        for row in range(self.rows):
            self.cells.append([Cell() for _ in range(self.cols)])

    def clear_line(self, row):
        self.cells[row] = [Cell() for _ in range(self.cols)]

    def get(self, row, col):
        return self.cells[row][col]

    def to_string(self, start_row = 0, start_col = 0, end_row = None, end_col = None):
        """ return screen contents as string """
        if end_row is None:
            end_row = self.rows - 1
        if end_col is None:
            end_col = self.cols - 1
        string = ''
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                string += self.cells[row][col].glyph
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
            for i in range(self.cols):
                sys.stdout.write('-')
            sys.stdout.write('\\' + ESC_GOTO_NEXT_LINE)

        last_fg_color = None
        last_bg_color = None
        last_bold = False

        for line in self.cells:
            if show_border:
                sys.stdout.write('|')

            for cell in line:

                # set bold
                if cell.bold != last_bold:
                    if cell.bold:
                        sys.stdout.write(ESC + '[1m')
                    else:
                        sys.stdout.write(ESC_FONT_NORMAL)
                        last_fg_color = None
                        last_bg_color = None
                    last_bold = cell.bold
 
                # set foreground color
                fg_color = cell.fg_color
                if fg_color != last_fg_color:
                    sys.stdout.write(ESC + '[' + str(fg_color) + 'm')
                    last_fg_color = fg_color

                # set background color
                bg_color = cell.bg_color
                if bg_color != last_bg_color:
                    sys.stdout.write(ESC + '[' + str(bg_color) + 'm')
                    last_bg_color = bg_color

                sys.stdout.write(cell.glyph)

            if show_border:
                sys.stdout.write(ESC_FONT_NORMAL)
                last_fg_color = None
                last_bg_color = None
                last_bold = False
                sys.stdout.write('|')

            sys.stdout.write(ESC_GOTO_NEXT_LINE)

        if show_border:
            sys.stdout.write('\\')
            for i in range(self.cols):
                sys.stdout.write('-')
            sys.stdout.write('/' + ESC_GOTO_NEXT_LINE)

        sys.stdout.flush()
               
        