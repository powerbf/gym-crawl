import gym
from gym import error, spaces, utils
from gym.utils import seeding
from subprocess import Popen, PIPE
from threading  import Thread
from queue import Queue, Empty
import re
import sys

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class CrawlEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    
    # dimensions of screen in characters (not pixels!)
    SCREEN_COLS = 80
    SCREEN_ROWS = 24

    # Keys
    NUMPAD_0 = '\x1bOp'
    NUMPAD_1 = '\x1bOq'
    NUMPAD_2 = '\x1bOr'
    NUMPAD_3 = '\x1bOs'
    NUMPAD_4 = '\x1bOt'
    NUMPAD_5 = '\x1bOu'
    NUMPAD_6 = '\x1bOv'
    NUMPAD_7 = '\x1bOw'
    NUMPAD_8 = '\x1bOx'
    NUMPAD_9 = '\x1bOy' 

    # commands
    WAIT = '.'    
    #GO_NORTH = 'k'
    #GO_SOUTH = 'j'
    #GO_EAST = 'h'
    #GO_WEST = 'l'
    #GO_NORTHWEST = 'y'
    #GO_NORTHEAST = 'u'
    #GO_SOUTHWEST = 'b'
    #GO_SOUTHEAST = 'n'

    GO_NORTH = NUMPAD_8
    GO_SOUTH = NUMPAD_2
    GO_EAST = NUMPAD_6
    GO_WEST = NUMPAD_4
    GO_SOUTHWEST = NUMPAD_1
    GO_SOUTHEAST = NUMPAD_3
    GO_NORTHWEST = NUMPAD_7
    GO_NORTHEAST = NUMPAD_9

    ACTION_LOOKUP = {
        0 : WAIT,
        1 : GO_NORTHWEST,
        2 : GO_NORTH,
        3 : GO_NORTHEAST,
        4 : GO_WEST,
        5 : GO_EAST,
        6 : GO_SOUTHWEST,
        7 : GO_SOUTH,
        8 : GO_SOUTHEAST,
    }

    def __init__(self):
        print('__init__')
        self.action_space = spaces.Discrete(9) 
        self.process = None
        self.queue = None
        self.render_file = None
        self.crawl_path = '/home/brian/crawl/0.24-ascii/bin'

        self.data = None
        self.frame = None
        self.row = 0
        self.col = 0
        self_frame_count = 0

    def __del__(self):
        self.close()

    def step(self, action):
        keys = self._action_to_keys(action)
        #print('Sending: ' + re.sub(r'\x1b', 'ESC', keys), file=sys.stderr)
        self.process.stdin.write(keys)
        self.process.stdin.flush()
        self._read_frame();
        ob = self.frame # TODO: process frame
        reward = self._get_reward;
        done = False # TODO:
        return ob, reward, done, {}

    def reset(self):
        print('CrawlEnv:reset')
        if self.process is not None:
            self.process.kill()

        cmd = [self.crawl_path + '/crawl', '-name', 'Lerny', '-species', 'Minotaur', '-background', 'Berserker']
        self.process = Popen(cmd, cwd=self.crawl_path, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True, universal_newlines=True)

        self.queue = Queue()
        thread = Thread(target=enqueue_output, args=(self.process.stdout, self.queue))
        thread.daemon = True # thread dies with the program
        thread.start()

        self.process.stdin.write('c') # choose axe
        self.process.stdin.flush()
        self._init_frame()
        self._read_frame();
        ob = self.frame # TODO: process frame
        reward = self._get_reward;
        done = False # TODO:
        return ob, reward, done, {}

    def _render_to_file(self, mode='human'):
        if self.render_file is None:
            self.render_file = open("render.txt", "w")
        for line in self.frame:
            self.render_file.write(line)
            self.render_file.write('\n')
        self.render_file.write('\n------------ END FRAME ({} lines) -----------\n'.format(len(self.frame)))

    def _render_to_screen(self, mode='human'):
        if self.frame is not None:
            #sys.stdout.write('\x1b[2J\x1b[H') # clear screen
            sys.stdout.write('\x1b[H')
            #print('---------------START FRAME {} ------------------'.format(self.frame_count))
            for row in self.frame:
                print(''.join(row))
            #for row in range(len(self.frame)):
            #    for col in range(len(self.frame[row])):
            #        sys.stdout.write('\x1b[' + str(row+1) + ';' + str(col+1) + 'H' + self.frame[row][col])
            print('---------------END FRAME {} ------------------'.format(self.frame_count))
        #if self.data is not None:
        #    sys.stdout.write(self.data)       

    def render(self, mode='human'):
        self._render_to_screen(mode)

    def close(self):
        print('CrawlEnv:close')
        if self.process is not None:
            self.render()
            self.process.kill()
            self.process = None
        if self.render_file is not None:
            self.render_file.close()
  
    def _action_to_keys(self, action):
        keys = self.ACTION_LOOKUP[action]
        return keys

    def _get_reward(self):
        return 1

    def _read_frame(self):
        # read without blocking
        try:
            data = self.queue.get_nowait() 
            #data = self.queue.get(timeout=.5)
        except Empty:
            return
        else:
            self._update_frame(data)

    def _update_frame(self, data):
        # update our internal representation of the screen
        # this is tricky because the raw data contains ASCII control sequences
        print('\nProcessing data: ' + re.sub(r'\x1b', 'ESC', data), file=sys.stderr)
        self.data = data
        self.frame_count += 1
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



