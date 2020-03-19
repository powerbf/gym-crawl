'''
Extract data from terminal
'''
import logging
import re

import gym_crawl.terminal as term
from gym_crawl.map import Color, Cell, Map

logger = logging.getLogger('term-parser')

# location of map within terminal
MAP_START_ROW = 0
MAP_END_ROW = 16
MAP_START_COL = 0
MAP_END_COL = 32 

# location of stat panel
STATS_START_ROW = 0
STATS_END_ROW = 8
STATS_START_COL = 37
STATS_END_COL = 79

def update_game_state(screen, game_state):
    """ Update the game state from the terminal screen"""
    _update_stats(screen, game_state)
    
    if game_state.on_main_screen:
        game_state.map = extract_map(screen)

def is_main_screen(screen):
    return _extract_stats_panel(screen) is not None

def extract_map(screen):
    """ Extract the map from the terminal data """
    # transform from row-major (row, col) to column-major (x, y)
    result = Map()
    result.cells = {}
    for col in range(MAP_START_COL, MAP_END_COL+1):
        x = col - MAP_START_COL
        result.cells[x] = {}
        for row in range(MAP_START_ROW, MAP_END_ROW+1):
            y = row - MAP_START_ROW
            term_cell = screen.cells[row][col]
            map_cell = _term_cell_to_map_cell(term_cell)
            result.cells[x][y] = map_cell
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Map:\n" + result.to_string())
    return result
                
# convert terminal foreground colours to map colours           
TERM_FG_COLOR_TO_MAP_COLOR = {
    term.FG_COLOR_BLACK: Color.BLACK,
    term.FG_COLOR_RED: Color.RED,
    term.FG_COLOR_GREEN: Color.GREEN,
    term.FG_COLOR_BROWN: Color.BROWN,
    term.FG_COLOR_BLUE: Color.BLUE,
    term.FG_COLOR_MAGENTA: Color.MAGENTA,
    term.FG_COLOR_CYAN: Color.CYAN,
    term.FG_COLOR_LIGHT_GRAY: Color.LIGHT_GRAY,
    term.FG_COLOR_DEFAULT: Color.LIGHT_GRAY,
    term.FG_COLOR_DARK_GRAY: Color.DARK_GRAY,
    term.FG_COLOR_LIGHT_RED: Color.LIGHT_RED,
    term.FG_COLOR_LIGHT_GREEN: Color.LIGHT_GREEN,
    term.FG_COLOR_YELLOW: Color.YELLOW,
    term.FG_COLOR_LIGHT_BLUE: Color.LIGHT_BLUE,
    term.FG_COLOR_LIGHT_MAGENTA: Color.LIGHT_MAGENTA,
    term.FG_COLOR_LIGHT_CYAN: Color.LIGHT_CYAN,
    term.FG_COLOR_WHITE: Color.WHITE
}

# convert terminal background colours to map colours           
TERM_BG_COLOR_TO_MAP_COLOR = {
    term.BG_COLOR_BLACK: Color.BLACK,
    term.BG_COLOR_RED: Color.RED,
    term.BG_COLOR_GREEN: Color.GREEN,
    term.BG_COLOR_BROWN: Color.BROWN,
    term.BG_COLOR_BLUE: Color.BLUE,
    term.BG_COLOR_MAGENTA: Color.MAGENTA,
    term.BG_COLOR_CYAN: Color.CYAN,
    term.BG_COLOR_LIGHT_GRAY: Color.LIGHT_GRAY,
    term.BG_COLOR_DEFAULT: Color.BLACK,
    term.BG_COLOR_DARK_GRAY: Color.DARK_GRAY,
    term.BG_COLOR_LIGHT_RED: Color.LIGHT_RED,
    term.BG_COLOR_LIGHT_GREEN: Color.LIGHT_GREEN,
    term.BG_COLOR_YELLOW: Color.YELLOW,
    term.BG_COLOR_LIGHT_BLUE: Color.LIGHT_BLUE,
    term.BG_COLOR_LIGHT_MAGENTA: Color.LIGHT_MAGENTA,
    term.BG_COLOR_LIGHT_CYAN: Color.LIGHT_CYAN,
    term.BG_COLOR_WHITE: Color.WHITE
}

def _term_cell_to_map_cell(term_cell):
    map_cell = Cell()
    
    map_cell.glyph = term_cell.glyph
    
    # foreground colour
    fg_color = term_cell.fg_color
    if fg_color == term.FG_COLOR_DEFAULT:
        fg_color = term.FG_COLOR_LIGHT_GRAY
    if term_cell.bold:
        fg_color += (term.FG_COLOR_DARK_GRAY - term.FG_COLOR_BLACK)
    map_cell.fg_color = TERM_FG_COLOR_TO_MAP_COLOR[fg_color]

    # background colour
    bg_color = term_cell.bg_color
    map_cell.bg_color = TERM_BG_COLOR_TO_MAP_COLOR[bg_color]
    
    return map_cell

def _extract_stats_panel(screen):
    stats = screen.to_string(STATS_START_ROW, STATS_START_COL, STATS_END_ROW, STATS_END_COL)
    if re.search(r'Health:.+Magic:.+AC:.+Str:', stats, re.DOTALL):
        logger.debug(stats)
        return stats
    else:
        return None
    
def _update_stats(screen, game_state):
    stats = _extract_stats_panel(screen)
    if stats is None:
        game_state.on_main_screen = False
        return
    
    game_state.on_main_screen = True

    stats = stats.replace('\n', '')
    
    # update hp/max_hp
    m = re.search(r'Health: *(\d+)\/(\d+)', stats)
    if m:
        if m.group(1):
            game_state.hp = int(m.group(1))
        if m.group(2):
            game_state.max_hp = int(m.group(2))

    # update mp/max_mp
    m = re.search(r'Magic: *(\d+)/(\d+)', stats)
    if m:
        if m.group(1):
            game_state.mp = int(m.group(1))
        if m.group(2):
            game_state.max_mp = int(m.group(1))

    # update experience level
    m = re.search(r'XL: *(\d+) *Next: *(\d+)', stats)
    if m and m.group(1) and m.group(2):
        game_state.xl = int(m.group(1))
        game_state.pcnt_next_xl = int(m.group(2))

    # update character stats
    m = re.search(r'AC: *(\d+)', stats)
    if m and m.group(1):
        game_state.ac = int(m.group(1))
    
    m = re.search(r'EV: *(\d+)', stats)
    if m and m.group(1):
        game_state.ev = int(m.group(1))

    m = re.search(r'SH: *(\d+)', stats)
    if m and m.group(1):
        game_state.sh = int(m.group(1))

    m = re.search(r'Str: *(\d+)', stats)
    if m and m.group(1):
        game_state.str = int(m.group(1))
    
    m = re.search(r'Int: *(\d+)', stats)
    if m and m.group(1):
        game_state.int = int(m.group(1))

    m = re.search(r'Dex: *(\d+)', stats)
    if m and m.group(1):
        game_state.dex = int(m.group(1))

    # Update time
    m = re.search(r'Time: *([\d\.]+)', stats)
    if m and m.group(1):
        game_state.time = float(m.group(1))

    # Update place
    m = re.search(r'Place: *([A-Za-z0-9\:]+)', stats)
    if m and m.group(1):
        game_state.place = m.group(1)

    # Update noise
    m = re.search(r'Noise: *(\=*)', stats)
    if m and m.group(1):
        game_state.noise = len(m.group(1))
    else:
        game_state.noise = 0

    if not game_state.started:
        # check if game has started now
        if game_state.max_hp != 0:
            game_state.started = True


