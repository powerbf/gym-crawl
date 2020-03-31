"""
Gym for DCSS terminal (a.k.a. console) version
"""

import gym
from gym import error, spaces, utils
from gym.utils import seeding
from subprocess import Popen, PIPE
from threading import Thread
import threading 
from queue import Queue, Empty
import copy
import logging
import os
import re
import time

import gym_crawl.terminal_capture as tc
from gym_crawl.chars import *
from gym_crawl.gamestate import GameState
import gym_crawl.terminal_parser as parser


LONG_RUNNING_ACTIONS = 'o5'

# Essential commands
ACTION_KEYS="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,<>\t" + ESC + ENTER
# Long-running actions
ACTION_KEYS += LONG_RUNNING_ACTIONS
# Non-essential info commands
#ACTION_KEYS += ';@$%^[}"' + CTRL_O + CTRL_X
# Some other useful commands
#ACTION_KEYS += '\\\'' + CTRL_A + CTRL_E


logger = logging.getLogger('crawl-terminal-env')

def enqueue_output_old(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def enqueue_output(out, queue):
    try:
        while not out.closed:
            out.flush()
            data = out.read1(1024*8).decode('utf-8', errors='replace')
            queue.put(data)
    except:
        pass
    finally:
        logger.debug("enqueue_ouput exiting")

class CrawlTerminalEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    
    # dimensions of screen in characters (not pixels!)
    SCREEN_COLS = 80
    SCREEN_ROWS = 24

    def __init__(self):
        logger.info('__init__')
        self.process = None
        self.queue = None
        self.render_file = None
        self.character_name = 'Bot'

        self.crawl_path = os.getenv('CRAWLDIR')
        if self.crawl_path is None:
            raise RuntimeError('You must set the CRAWLDIR environment variable with the location of your DCSS installation.')
        self.crawl_bin_dir = self.crawl_path + '/bin'
        self.crawl_exe = self.crawl_bin_dir + '/crawl'
        if not os.path.exists(self.crawl_exe):
            raise RuntimeError(self.crawl_exe + ' does not exist. Have you set the CRAWLDIR environment variable correctly?')

        self.action_keys = ACTION_KEYS
        self.action_space = spaces.Discrete(len(self.action_keys)) 

        self.episode = 0
        self.terminal = None
        self.frame_count = 0
        self.steps = 0
        self.stuck_steps = 0
        self.error = False
        self.last_sent = ''
        self.ready = False
        self.reward = 0
        self.score = 0
        self.game_state = GameState()

        self.player_row = None
        self.player_col = None

        # timing
        self.max_read_time = 0.0
        self.max_ready_time = 0.0
        self.read_timeout = 0.1
        self.long_running_read_timeout = 5.0

    def __del__(self):
        #self.close() # logging will throw an exception at this point
        pass

    def set_character_name(self, value):
        self.character_name = value

    def get_character_name(self):
        return self.character_name

    def set_action_keys(self, keys):
        """Override the default list of possible actions"""
        self.action_keys = keys
        self.action_space = spaces.Discrete(len(self.action_keys)) 

    def get_action_keys(self):
        """Get the current list of possible actions"""
        return self.action_keys

    def action_to_keys(self, action):
        """ Translate an action space index (int) into actual key(s)"""
        keys = self.action_keys[action]
        return keys

    def reset(self):
        logger.info('reset')
        self.close()

        self.episode += 1

        self.terminal = tc.TerminalCapture()
        self.frame_count = 0
        self.steps = 0
        self.stuck_steps = 0
        self.error = False
        self.on_main_screen = False
        self.game_state = GameState()
        self.score = 0

        self.max_read_time = 0.0
        self.max_ready_time = 0.0
        self.ready = False

        crawl_saves_dir = './saves'
        crawl_save_file = crawl_saves_dir + '/' + self.character_name + '.cs'

        if os.path.exists(crawl_save_file):
            os.remove(crawl_save_file)

        cmd = [self.crawl_exe, '-dir', '.', '-rc', './crawlrc', '-name', self.character_name, '-species', 'Minotaur', '-background', 'Berserker']
        self.process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True, universal_newlines=True)

        # detach process stdout from buffer
        self.process.stdout = self.process.stdout.detach()

        self.queue = Queue()
        thread = Thread(target=enqueue_output, args=(self.process.stdout, self.queue))
        thread.daemon = True # thread dies with the program
        thread.start()
        
        weapon_chosen = False
        game_started = False
        loop_count = 0
        while not game_started:
            loop_count += 1
            if loop_count >= 30:
                logger.error("Failed to start episode. Screen dump:" + self.terminal.screen.to_string())
                self.error = True
                break
            self._read_frame();
            screen_contents = self.terminal.screen.to_string()
            if 'Found a staircase leading out of the dungeon' in screen_contents:
                game_started = True
            elif not weapon_chosen and 'You have a choice of weapons' in screen_contents:  
                self._send_chars('c') # choose axe
                weapon_chosen = True

        done = (self.game_state.is_finished() or self.error)
        return self.game_state, self.reward, done, self.terminal.screen

    def step(self, action):
        self.steps += 1
        logger.debug("Step {} start: self.ready={}, screen:\n".format(self.steps, self.ready) + self.terminal.screen.to_string())

        prev_time = self.game_state.time

        # perform action
        keys = self.action_to_keys(action)
        self._send_chars(keys)

        if not self.error:
            self._read_frame();

        if self.game_state.time == prev_time:
            self.stuck_steps += 1
        else:
            self.stuck_steps = 0

        self.score += self.reward

        done = self.error or self.game_state.is_finished()
        if not done and self.stuck_steps >= 1000:
            logger.info('Stuck for 1000 steps. Giving up. Screen dump:\n' + self.terminal.screen.to_string())
            done = True

        if self.steps % 100 == 0:
            logger.info('Step {}: Game Time={}'.format(self.steps, self.game_state.time))

        return self.game_state, self.reward, done, self.terminal.screen

    def _render_to_file(self, mode='human'):
        if self.render_file is None:
            self.render_file = open("render.txt", "w")
        for line in self.terminal.screen.cells:
            self.render_file.write(line)
            self.render_file.write('\n')
        self.render_file.write('\n------------ END FRAME ({} lines) -----------\n'.format(self.terminal.screen.rows))

    def _render_to_screen(self, mode='human'):
        if self.terminal is not None:
            self.terminal.screen.render(1, 1)
            action = tc.make_printable(self.last_sent)
            print('Episode: {}  Step: {:<6d}  Action: {:<5}  Reward: {:<7d}  Cumulative score: {:<10d}'.format(self.episode, self.steps, action, self.reward, self.score))

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
        if self.process is not None:
            self.process.stdout.close() # cause reading thread to end
        if self.render_file is not None:
            self.render_file.close()
        logger.debug("Thread count: {}".format(threading.active_count()))

    def _send_chars(self, chars):
        """ Send characters to the crawl process
        """
        logger.debug('Sending: ' + tc.make_printable(chars))
        self.last_sent = chars
        try:
            self.process.stdin.write(chars)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(str(e))
            logger.error("I think I overran crawl's input buffer. This is where I was:\n" + self.terminal.screen.to_string())
            self.error = True

    def _read_data_chunk(self, read_timeout):
        try:
            self.process.stdout.flush()
            #data_chunk = self.queue.get_nowait()
            data_chunk = self.queue.get(timeout=read_timeout)
        except Empty:
            return None
        else:
            return data_chunk
    

    def _is_ready(self, data):

        # remove newlines because they mess with regular expression matching
        data = data.replace('\n', '')

        # when drawing main screen, cursor is left at @ position
        if self.player_row is None or self.player_col is None:
            self._find_player_symbol()
        if self.player_row is not None and self.player_col is not None:
            if data.endswith('\x1b[{};{}H'.format(self.player_row+1, self.player_col+1)):
                return True

        # check for known end of screen strings
        
        # abilities screen
        if "to toggle between ability selection and description." in data:
            return True

        # religion screen
        if "Powers|Wrath" in data:
            return True

        # skills screen
        if "costs|targets" in data:
            return True

        # spells (M) screen
        if "Describe|Hide|Show" in data:
            return True

        # cast spell (z/Z) screen
        if "to toggle spell view." in data:
            return True

        # character description screen
        if re.search(r'HPRegen .*MPRegen .*@: .*A: ', data):
            return True

        # monster description screen when monster has spell
        if "shown in red if you are in range." in data:
            return True

        return False


    def _read_frame(self):
        self.reward = 0
        data = ''
        got_data = False
        done = False
        ready = False
        prev_ready = self.ready
        loop_count = 0
        chars = tc.make_printable(self.last_sent)

        long_running_action = False
        read_timeout = self.read_timeout
        if self.on_main_screen and prev_ready and self.last_sent in LONG_RUNNING_ACTIONS:
            long_running_action = True
            read_timeout = self.long_running_read_timeout
            logger.debug("Step {}: Starting long running operation: {}".format(self.steps, chars))

        read_time = 0.0
        ready_time = None
        start_time = time.perf_counter()
        while not done:
            loop_count += 1
            data_chunk = self._read_data_chunk(0.01)
            elapsed_time = (time.perf_counter() - start_time)
            if data_chunk is None:
                if elapsed_time >= read_timeout:
                    if long_running_action:
                        logger.warn("Step {}: Timeout on action '{}': {:.3f} seconds. Screen dump:\n".format(self.steps, chars, elapsed_time) + self.terminal.screen.to_string())
                    done = True
            else:
                read_time = (time.perf_counter() - start_time)
                logger.debug('Got {} bytes of data'.format(len(data_chunk)))
                data += data_chunk
                got_data = True
                # handle prompts, so we don't get stuck
                if  '--more--' in data_chunk:
                    logger.info('Detected --more-- prompt')
                    self._send_chars(' ')
                elif "Inscribe with what?" in data_chunk or "Replace inscription with what?" in data_chunk:
                    # Nip this in the bud because it can crash crawl if too many characters are sent
                    logger.debug('Detected inscriptions prompt')
                    self._send_chars(ESC)
                elif "Drop what? 0/52 slots" in data_chunk:
                    # This can also crash crawl if too many characters are sent
                    logger.debug('Detected drop prompt for empty inventory')
                    self._send_chars(ESC)
                elif self._is_ready(data):
                    ready_time = read_time
                    ready = True
                    done = True
        if got_data:
            logger.debug('read_loop_count={}'.format(loop_count))
            if self.steps >= 1 and not long_running_action:
                if read_time > self.max_read_time:
                    self.max_read_time = read_time
                    action = tc.make_printable(self.last_sent)
                    logger.info("Step {}: Max redraw time: {:.3f} seconds, action={}".format(self.steps, read_time, action))
                if ready_time is not None and ready_time > self.max_ready_time:
                    self.max_ready_time = ready_time
                    action = tc.make_printable(self.last_sent)
                    logger.info("Step {}: Max known ready time: {:.3f} seconds, action={}".format(self.steps, self.max_ready_time, action))

            self.frame_count += 1
            self._process_data(data)

        self.ready = ready

    def _process_data(self, data):
        # save old game state
        prev_state = self.game_state
        self.game_state = copy.deepcopy(prev_state)
        
        # capture screen update
        self.terminal.handle_output(data)

        # get new state
        parser.update_game_state(self.terminal.screen, self.game_state)
        
        if not prev_state.started:
            if self.game_state.started:
                # reward navigation through start menu to actual game
                logger.debug('Reward for starting: 1')
                self.reward = 1
            else:
                logger.debug('Reward for not starting: 0')
                self.reward = 0
            return
        
        # check for game end
        if 'You have escaped' in data:
            if self.game_state.has_orb:
                self.game_state.won = True
                logger.debug('Reward for winning: +1e6')
                self.reward = 1000000
            else:
                self.game_state.escaped = True
                logger.debug('Reward for leaving without orb: -1e6')
                self.reward = -1000000
        elif 'You die' in data:
            logger.info("Step {}: Died".format(self.steps))
            self.game_state.died = True

        if self.game_state.is_finished():
            return

        if not self.game_state.has_orb:
            if 'You pick up the Orb of Zot' in data:
                logger.info("Step {}: Picked up the Orb".format(self.steps))
                self.reward += 10000
                self.game_state.has_orb = True

        # check for experience gain
        xl = self.game_state.xl
        prev_xl = prev_state.xl
        pcnt_next = self.game_state.pcnt_next_xl
        prev_pcnt_next = prev_state.pcnt_next_xl
        
        xp_reward = (xl - prev_xl) * 100
        xp_reward += pcnt_next - prev_pcnt_next
        
        if xp_reward != 0:
            logger.debug('Reward for percent XP: {}'.format(xp_reward))
            self.reward += xp_reward
        
        # Check time
        if self.game_state.time > prev_state.time:
            logger.debug('Time: ' + str(self.game_state.time))


    def _find_player_symbol(self):
        """Find the @"""
        for row in range(self.terminal.screen.rows):
            for col in range(self.terminal.screen.cols):
                if self.terminal.screen.cells[row][col].glyph == '@':
                    logger.info("@ found at {},{}".format(row+1, col+1))
                    self.player_row = row
                    self.player_col = col
                    return


