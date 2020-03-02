import gym
from gym import error, spaces, utils
from gym.utils import seeding
from subprocess import Popen, PIPE
from threading  import Thread
from queue import Queue, Empty
import sys

from gym_crawl.terminal_capture import TerminalCapture

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

        self.frame = TerminalCapture()
        self.frame_count = 0

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
            self.frame.render(1, 1)
            print('---------------END FRAME {} ------------------'.format(self.frame_count))

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
            self.frame_count += 1
            self.frame.handle_output(data)

