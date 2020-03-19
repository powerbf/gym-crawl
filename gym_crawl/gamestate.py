'''
Class representing current game state
'''

class GameState:
    
    def __init__(self):
        self.on_main_screen = False
        
        self.started = False
        self.won = False
        self.died = False
        self.escaped = False # escaped without orb
        
        self.has_orb = False
        self.runes = []
        
        self.map = None
        
        self.hp = 0
        self.max_hp = 0
        self.mp = 0
        self.max_mp = 0
        
        self.str = 0 # strength
        self.int = 0 # intelligence
        self.dex = 0 # dexterity
        
        self.ac = 0 # armour class
        self.ev = 0 # evasion
        self.sh = 0 # shielding
        
        self.xl = 0 # experience level (1-27)
        self.pcnt_next_xl = 0
        
        self.noise = 0  # noise level (0-9)
        self.place = '' # place (e.g. Dungeon:1)
        self.time = 0.0

    def is_finished(self):
        return self.won or self.died or self.escaped
    
    def get_num_runes(self):
        return len(self.runes)
    