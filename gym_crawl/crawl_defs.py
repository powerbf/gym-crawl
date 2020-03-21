'''
Some info about crawl
'''

DCHAR_WALL = '#'
DCHAR_PERMAWALL = '\x2593'  # ▓
DCHAR_WALL_MAGIC = '*'
DCHAR_FLOOR = '.'
DCHAR_FLOOR_MAGIC = ','
DCHAR_DOOR_OPEN = '\\'
DCHAR_DOOR_CLOSED = '+'
DCHAR_TRAP = '^'
DCHAR_STAIRS_DOWN = '>'
DCHAR_STAIRS_UP = '<'
DCHAR_GRATE = '#'
DCHAR_ALTAR = '_'
DCHAR_ARCH = '\x2229'
DCHAR_FOUNTAIN = '\x2320'
DCHAR_WAVY = '\x2248'
DCHAR_STATUE = '8'
DCHAR_INVIS_EXPOSED = '{'

DCHAR_ITEM_DETECTED = '\x2206'  # ∆
DCHAR_ITEM_DETECTED_WIN = '\x2302'  # ⌂
DCHAR_ITEM_ORB = '0'
DCHAR_ITEM_RUNE = '\x03c6'
DCHAR_ITEM_WEAPON = ')'
DCHAR_ITEM_ARMOUR = '['
DCHAR_ITEM_WAND = '/'
DCHAR_ITEM_FOOD = '%'
DCHAR_ITEM_SCROLL = '?'
DCHAR_ITEM_RING = '='
DCHAR_ITEM_POTION = '!'
DCHAR_ITEM_MISSILE = '('
DCHAR_ITEM_BOOK = ':'
DCHAR_ITEM_STAFF = '|'
DCHAR_ITEM_ROD = '\\'
DCHAR_ITEM_MISCELLANY = '}'
DCHAR_ITEM_CORPSE = '\x2020'   # †
DCHAR_ITEM_SKELETON = '\xf7'   # ÷
DCHAR_ITEM_GOLD = '$'
DCHAR_ITEM_AMULET = '"'

DCHAR_CLOUD = '\xa7'           # §
DCHAR_CLOUD_WEAK = '\x263c'    # ☼
DCHAR_CLOUD_FADING = '\x25CB'  # ○
DCHAR_CLOUD_TERMINAL = '\xB0'  # °

DCHAR_TREE = '\x2663'          # ♣

DCHAR_TELEPORTER = '\xa9'
DCHAR_TRANSPORTER = '\xa9'
DCHAR_TRANSPORTER_LANDING = '\xa9'

DCHAR_SPACE = ' '
DCHAR_FIRED_BOLT = '#'
DCHAR_FIRED_ZAP =  '*'
DCHAR_FIRED_BURST = '\xf7'   # ÷
DCHAR_FIRED_DEBUG = 'X'
DCHAR_FIRED_MISSILE = '`'
DCHAR_EXPLOSION = '#'

DCHAR_FRAME_HORIZ = '\x2550' # ═
DCHAR_FRAME_VERT = '\x2551'  # ║
DCHAR_FRAME_TL = '\x2554'    # ╔
DCHAR_FRAME_TR ='\x2557'     # ╗
DCHAR_FRAME_BL = '\x255a'    # ╚
DCHAR_FRAME_BR = '\x255d'    # ╝

DCHAR_DRAW_HORIZ = '\x2500' # ─
DCHAR_DRAW_VERT = '\x2502'  # │
DCHAR_DRAW_SLASH = '/'
DCHAR_DRAW_BACKSLASH = '\\'
DCHAR_DRAW_TL = '\x250c'    # ┌
DCHAR_DRAW_TR = '\x2510'    # ┐
DCHAR_DRAW_BL = '\x2514'    # └
DCHAR_DRAW_BR = '\x2518'    # ┘
DCHAR_DRAW_DOWN = 'V'
DCHAR_DRAW_UP = '\x39b'     # Λ
DCHAR_DRAW_RIGHT = '>'
DCHAR_DRAW_LEFT = '<'


MONSTER_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ12345679&@;{'

# '8' is golem, crystal guardian and others, but is more commonly a statue, 
# * is orb of fire, tentacles and others, but is also a magic wall, 
# '(' is dancing/spectral weapon, but also missile
AMBIGUOUS_MONSTER_CHARS = '8*('

# Item glyphs (excluding rods, which are obsolete and share a glyph with open doors)
NORMAL_ITEM_CHARS = ')[/%?=!(:|}$"' + DCHAR_ITEM_DETECTED + DCHAR_ITEM_DETECTED_WIN
QUEST_ITEM_CHARS = DCHAR_ITEM_RUNE + DCHAR_ITEM_ORB # need these to win the game
UNGETABLE_ITEM_CHARS = DCHAR_ITEM_CORPSE + DCHAR_ITEM_SKELETON

# I think wavy = lava, deep water and shallow water - the last one is passable
IMPASSABLE_CHARS = DCHAR_WALL + DCHAR_PERMAWALL + DCHAR_WALL_MAGIC + DCHAR_TREE \
    + DCHAR_STATUE + DCHAR_WAVY
