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
        self.dungeon_feature = None
        self.map_feature = None
        self.tile = None
        

class Map:
    
    def __init__(self):
        # array of cells, indexed by x, y
        self.cells = {}
        self.player_pos = None

    def to_string(self):
        """ return map contents as string """
        
        xmin = min(self.cells.keys())
        xmax = max(self.cells.keys())
        
        ymin = 0
        ymax = 0
        for x, column in self.cells.items():
            ymin = min([ymin, min(column.keys())])
            ymax = max([ymax, max(column.keys())])
        
        string = ''
        for y in range(ymin, ymax+1):
            if string != '':
                string += '\n'
            for x in range(xmin, xmax+1):
                glyph = ' '
                if x in self.cells:
                    column = self.cells[x]
                    if y in column:
                        cell = column[y]
                        if cell and cell.glyph:
                            glyph = cell.glyph
                string += glyph

        return string

    def clear(self):
        self.cells = {}
    
    def set_cell(self, x, y, cell):
        if not x in self.cells:
            self.cells[x] = {}
        self.cells[x][y] = cell
    
    def get_cell(self, x, y):
        if x in self.cells and y in self.cells[x]:
            return self.cells[x][y]
        else:
            return None
    