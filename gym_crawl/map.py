'''
DCSS Map
'''
from enum import Enum
import logging

logger = logging.getLogger('map')


# define colours in the same order as DCSS defines.h
class Color(Enum):
    BLACK = 0
    BLUE = 1
    GREEN = 2
    CYAN = 3
    RED = 4
    MAGENTA = 5
    BROWN = 6
    LIGHT_GRAY = 7
    DARK_GRAY = 8
    LIGHT_BLUE = 9
    LIGHT_GREEN = 10
    LIGHT_CYAN = 11
    LIGHT_RED = 12
    LIGHT_MAGENTA = 13
    YELLOW = 14
    WHITE = 15


class Cell:
    """ A cell in the map """

    def __init__(self):
        self.glyph = None
        self.fg_color = Color.LIGHT_GRAY
        self.bg_color = Color.BLACK
        

class Map:
    
    def __init__(self):
        # array of cells, indexed by x, y
        self.cells = None

    def to_string(self):
        """ return map contents as string """
        lines = {}
        for x, column in sorted(self.cells.items()):
            for y, cell in sorted(column.items()):
                if not y in lines:
                    lines[y] = ''
                lines[y] += cell.glyph
        
        string = ''
        for y, line in sorted(lines.items()):
            string += line + '\n'
        return string
