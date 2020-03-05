import gym
from gym import error, spaces, utils
from gym.utils import seeding
from subprocess import Popen, PIPE
from threading  import Thread
from queue import Queue, Empty
import logging
import os
import re
import sys
import time
import gym_crawl.terminal_capture as tc

# Keys
ESC = tc.ESC
CTRL_A = '\x01'
CTRL_E = '\x05'
CTRL_O = '\x1F'
CTRL_P = '\x10'
CTRL_Q = '\x11'
CTRL_X = '\x18'

logger = logging.getLogger('crawl-env')

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class CrawlEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    
    # dimensions of screen in characters (not pixels!)
    SCREEN_COLS = 80
    SCREEN_ROWS = 24

    # Essential commands
    ACTION_KEYS="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,<>';" + CTRL_X + ESC
    # Auto actions
    ACTION_KEYS += '5o\t'
    # Non-essential info commands
    ACTION_KEYS += '@$%^[}"' + CTRL_O + CTRL_P
    # Some other useful commands
    #ACTION_KEYS += '\\' + CTRL_A + CTRL_E


    def __init__(self):
        logger.info('__init__')
        self.action_space = spaces.Discrete(len(self.ACTION_KEYS)) 
        self.process = None
        self.queue = None
        self.render_file = None
        self.crawl_path = '/home/brian/crawl/0.24-ascii'
        self.character_name = 'Lerny'

        self.frame = None
        self.frame_count = 0
        self.steps = 0
        self.stuck_steps = 0
        self.error = False
        
        self._init_game_state()
        self.reward = 0

    def __del__(self):
        #self.close() # logging will throw an exception at this point
        pass

    def reset(self):
        logger.info('reset')
        self.close()

        self.frame = tc.TerminalCapture()
        self.frame_count = 0
        self.steps = 0
        self.stuck_steps = 0
        self.error = False
        self._init_game_state()

        crawl_bin_dir = self.crawl_path + '/bin'
        crawl_saves_dir = self.crawl_path + '/bin/saves'
        crawl_save_file = crawl_saves_dir + '/' + self.character_name + '.cs'

        if os.path.exists(crawl_save_file):
            os.remove(crawl_save_file)

        cmd = [crawl_bin_dir + '/crawl', '-name', self.character_name, '-species', 'Minotaur', '-background', 'Berserker']
        self.process = Popen(cmd, cwd=crawl_bin_dir, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True, universal_newlines=True)

        self.queue = Queue()
        thread = Thread(target=enqueue_output, args=(self.process.stdout, self.queue))
        thread.daemon = True # thread dies with the program
        thread.start()

        self._send_chars('c') # choose axe

        self._read_frame();            

        return self.frame, self.reward, self.game_state['finished'], self.game_state

    def step(self, action):
        # perform action
        self.steps += 1
        keys = self._action_to_keys(action)
        self._send_chars(keys)

        self._read_frame();

        done = self.error or self.game_state['finished']
        if not done and self.stuck_steps >= 1000:
            logger.info('Stuck for 1000 steps. Giving up. Screen dump:\n' + self.frame.to_string())
            done = True

        if self.steps % 1000 == 0:
            logger.info('Step {}: Time={}'.format(self.steps, self.game_state['Time']))

        return self.frame, self.reward, done, self.game_state

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
            print('FRAME_COUNT: {}    '.format(self.frame_count))

    def render(self, mode='human'):
        self._render_to_screen(mode)

    def close(self):
        if self.process is not None and self.process.poll() is None:
            try:
                self._send_chars(ESC+ESC+ESC + CTRL_Q + 'yes' + ESC+ESC+ESC)
                self.process.wait(timeout=0.5)
            except:
                logger.info('Killing process')
                self.process.kill() # die horribly
        if self.render_file is not None:
            self.render_file.close()
  
    def _action_to_keys(self, action):
        keys = self.ACTION_KEYS[action]
        return keys

    def _send_chars(self, chars):
        """ Send characters to the crawl process
        """
        logger.debug('Sending: ' + tc.make_printable(chars))
        try:
            self.process.stdin.write(chars)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(str(e))
            logger.error("I think I overran crawl's input buffer. This is where I was:\n" + self.frame.to_string())
            self.error = True

    def _read_frame(self):
        self.reward = 0
        got_data = False
        done = False
        while not done:
            try:
                #data = self.queue.get_nowait()
                data = self.queue.get(timeout=.001)
            except Empty:
                done = True
            else:
                logger.debug('Got {} bytes of data'.format(len(data)))
                got_data = True
                self._process_data(data)
                # handle prompts, so we don't get stuck
                if  '--more--' in data:
                    logger.info('Detected --more-- prompt')
                    self._send_chars(' ')
                elif "Inscribe with what?" in data or "Replace inscription with what?" in data:
                    # Nip this in the bud because it can crash crawl if too many characters are sent
                    logger.debug('Detected inscriptions prompt')
                    self._send_chars(ESC)
                elif "Drop what? 0/52 slots" in data:
                    # This can alos crash crawl if too many characters are sent
                    logger.debug('Detected drop prompt for empty inventory')
                    self._send_chars(ESC)
        if got_data:
            self.frame_count += 1
            self._update_game_state()
            self.stuck_steps = 0
        else:
            self.stuck_steps += 1
            time.sleep(0.001)

    def _process_data(self, data):
        # capture screen update
        self.frame.handle_output(data)

        if self.game_state['finished'] or not self.game_state['started']:
            return

        # check for game end
        if 'You have escaped' in data:
            self.game_state['finished'] = True
            if self.game_state['Has Orb']:
                self.game_state['won'] = True
                logger.debug('Reward for winning: +1e6')
                self.reward = 1000000
            else:
                logger.debug('Reward for leaving without orb: -1e6')
                self.reward = -1000000
        elif 'You die' in data:
            self.game_state['finished'] = True

        if self.game_state['finished']:
            return

        if 'You pick up the Orb of Zot' in data:
            self.game_state['Has Orb'] = True

    def _update_game_state(self):
        display = self.frame.to_string()

        # check if we are on main game screen
        if not re.search(r'Health:.+Magic:.+AC:.+Str:', display.replace('\n', '')):
            return
        
        # update hp/max_hp
        m = re.search(r'Health: *(\d+)\/(\d+)', display)
        if m:
            hp = int(m.group(1))
            prev_hp = self.game_state['HP']
            if hp != prev_hp:
                self.game_state['HP'] = hp

            max_hp = int(m.group(2))
            prev_max_hp = self.game_state['Max HP']
            if max_hp != prev_max_hp:
                if self.game_state['started']:
                    logger.debug('Reward for increased max HP: {}'.format(max_hp - prev_max_hp))
                    self.reward += (max_hp - prev_max_hp)
                self.game_state['Max HP'] = max_hp

        # update mp/max_mp
        m = re.search(r'Magic: *(\d+)/(\d+)', display)
        if m:
            mp = int(m.group(1))
            prev_mp = self.game_state['MP']
            if mp != prev_mp:
                self.game_state['MP'] = mp

            max_mp = int(m.group(2))
            prev_max_mp = self.game_state['Max MP']
            if max_mp != prev_max_mp:
                self.game_state['Max MP'] = max_mp

        # update experience level
        m = re.search(r'XL: *(\d+) *Next: *(\d+)', display)
        if m and m.group(1) and m.group(2):
            xl = int(m.group(1))
            prev_xl = self.game_state['XL']
            if xl != prev_xl:
                if self.game_state['started']:
                    logger.debug('Reward for XL: {}'.format(xl - prev_xl))
                    self.reward += (xl - prev_xl) * 100
                self.game_state['XL'] = xl

            pcnt_next_xl = int(m.group(2))
            prev_pcnt_next_xl = self.game_state['Percent Next XL']
            if pcnt_next_xl != prev_pcnt_next_xl:
                if self.game_state['started']:
                    logger.debug('Reward for percent XL: {}'.format(pcnt_next_xl - prev_pcnt_next_xl))
                    self.reward += (pcnt_next_xl - prev_pcnt_next_xl)
                self.game_state['Percent Next XL'] = pcnt_next_xl

        # update character stats
        m = re.search(r'AC: *(\d+)', display)
        if m:
            self.game_state['AC'] = int(m.group(1))
        
        m = re.search(r'EV: *(\d+)', display)
        if m:
            self.game_state['EV'] = int(m.group(1))

        m = re.search(r'SH: *(\d+)', display)
        if m:
            self.game_state['SH'] = int(m.group(1))

        m = re.search(r'Str: *(\d+)', display)
        if m:
            self.game_state['Str'] = int(m.group(1))
        
        m = re.search(r'Int: *(\d+)', display)
        if m:
            self.game_state['Int'] = int(m.group(1))

        m = re.search(r'Dex: *(\d+)', display)
        if m:
            self.game_state['Dex'] = int(m.group(1))

        # Update time
        m = re.search(r'Time: *([\d\.]+)', display)
        if m:
            time = float(m.group(1))
            prev_time = self.game_state['Time']
            if time > prev_time:
                logger.debug('Time: ' + str(time))
                # reward actions that advance time (i.e. legal moves)
                logger.debug('Reward for time: +1')
                self.reward += 1
                self.game_state['Time'] = time

        # Update place
        m = re.search(r'Place: *([A-Za-z0-9\:]+)', display)
        if m:
            self.game_state['Place'] = m.group(1)

        # Update noise
        m = re.search(r'Noise: *(\=*)', display)
        if m:
            self.game_state['Noise'] = len(m.group(1))

        if not self.game_state['started']:
            # check if game has started now
            if self.game_state['Max HP'] != 0:
                self.game_state['started'] = True
                # reward navigation through start menu to actual game
                logger.debug('Reward for starting: 1')
                self.reward = 1
            else:
                logger.debug('Reward for not starting: 0')
                self.reward = 0
                self.stuck_steps += 1

    def _init_game_state(self):
        state = {}
        state['started'] = False
        state['finished'] = False
        state['Has Orb'] = False
        state['won'] = False
        state['Time'] = 0.0
        state['Place'] = ''
        state['Noise'] = 0
        state['XL'] = 1
        state['Percent Next XL'] = 0
        state['HP'] = 0
        state['Max HP'] = 0
        state['MP'] = 0
        state['Max MP'] = 0
        state['AC'] = 0
        state['EV'] = 0
        state['SH'] = 0
        state['Str'] = 0
        state['Int'] = 0
        state['Dex'] = 0
        self.game_state = state

