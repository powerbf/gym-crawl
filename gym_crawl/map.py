'''
DCSS Map
'''

import logging
from .crawl_defs import *


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

    FEATURE_CHARS = {
        MapFeature.UNSEEN : '?',
        MapFeature.FLOOR : '.',
        MapFeature.WALL : '#',
        MapFeature.MAP_FLOOR : '.',
        MapFeature.MAP_WALL : '#',
        MapFeature.DOOR : '+',
        MapFeature.ITEM : '%',
        MapFeature.MONS_FRIENDLY : 'f',
        MapFeature.MONS_PEACEFUL : 'p',
        MapFeature.MONS_NEUTRAL : 'n',
        MapFeature.MONS_HOSTILE : 'h',
        MapFeature.MONS_NO_EXP : 'x',
        MapFeature.STAIR_UP : '<',
        MapFeature.STAIR_DOWN : '>',
        MapFeature.STAIR_BRANCH : '^',
        MapFeature.FEATURE : DCHAR_FOUNTAIN,
        MapFeature.WATER : '~',
        MapFeature.LAVA : 'L',
        MapFeature.TRAP : 'T',
        MapFeature.EXCL_ROOT : '0',
        MapFeature.EXCL : 'X',
        MapFeature.PLAYER : '@',
        MapFeature.DEEP_WATER : 'W',
        MapFeature.PORTAL : 'P',
        MapFeature.TRANSPORTER : 'O',
        MapFeature.TRANSPORTER_LANDING : 'o',
        MapFeature.EXPLORE_HORIZON : '\xa4' # ¤
    }
    
    def get_map_feature_as_glyph(self):
        if self.map_feature == None:
            return ' '
        elif self.map_feature in Cell.FEATURE_CHARS:
            return Cell.FEATURE_CHARS[self.map_feature]
        else:
            return '\xb7f' # ¿
        

class Map:
    
    def __init__(self):
        # array of cells, indexed by x, y
        self.cells = {}
        self.player_pos = None

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

    def to_string(self, use_map_feature=False):
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
                cell = self.get_cell(x, y)
                if cell:
                    if use_map_feature:
                        glyph = cell.get_map_feature_as_glyph()
                    else:
                        if cell.glyph:
                            glyph = cell.glyph
                        elif cell.map_feature: 
                            if cell.map_feature == MapFeature.EXPLORE_HORIZON:
                                glyph = '\xa4' # ¤
                                #glyph = '\xb7f' # ¿
                string += glyph

        return string
