'''
DCSS Map
'''

import logging
from .crawl_defs import CharAttribute, Color, MapFeature

logger = logging.getLogger('map')


class Cell:
    """ A cell in the map """

    def __init__(self):
        self.glyph = None
        self.fg_color = Color.LIGHT_GRAY
        self.bg_color = Color.BLACK
        self.char_attr = CharAttribute.NORMAL
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
                        elif cell and cell.map_feature: 
                            if cell.map_feature == MapFeature.MF_EXPLORE_HORIZON:
                                glyph = '\xa4' # ¤
                                #glyph = '\xb7f' # ¿
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
    