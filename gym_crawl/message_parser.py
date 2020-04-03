'''
Parse message from websocket version of Crawl
'''

import logging

from gym_crawl.crawl_defs import *
from gym_crawl.map import Color, Cell, Map
from gym_crawl.gamestate import *


logger = logging.getLogger('msg-parser')

def update_game_state(msg, game_state):
    if msg['msg'] == 'player':
        update_player(msg, game_state)
    elif msg['msg'] == 'map':
        if game_state.map is None:
            game_state.map = Map()
        update_map(msg, game_state.map)
        
def update_player(msg, game_state):
    pass

def update_map(msg, map):
    if 'clear' in msg and msg['clear'] == True:
        map.clear()
    
    x = 0
    y = 0
    for cell in msg['cells']:
        if 'x' in cell:
            x = cell['x']
        else:
            x += 1
        if 'y' in cell:
            y = cell['y']
        
        map_cell = map.get_cell(x, y)
        if map_cell is None:
            map_cell = Cell()
            map.set_cell(x, y, map_cell)
        update_cell(cell, map_cell)

    logger.info("Map:\n" + map.to_string())

def update_cell(src, dest):
    '''Update cell from message representation'''
    if 'f' in src:
        dest.dungeon_feature = src['f']
    if 'mf' in src:
        dest.map_feature = MapFeature(src['mf'])
    if 'g' in src:
        dest.glyph = src['g']
    if 'col' in src:
        dest.fg_color = src['col']
    if 't' in src:
        dest.tile = src['t']
    