'''
Controller for DCSS
'''

from abc import ABC, abstractmethod
from enum import Enum
import logging
import os
from queue import Queue, Empty
import subprocess as subp
import time

from gym_crawl import crawl_socket
from gym_crawl.chars import CTRL_Q, ESC
from gym_crawl.gamestate import *
from gym_crawl.map import Color, Cell, Map
import gym_crawl.message_parser as parser
from gym_crawl.util import *


# initialize logger
logger = logging.getLogger('crawl-controller')

    
class ControllerState(Enum):
    NotConnected = 0,
    Connected = 1, # connected, but not logged in
    LoggedIn = 3,
    Lobby = 4, # Lobby (logged in)
    StartingGame = 5,
    InGame = 6,
    Quitting = 7


class CrawlController(ABC):
    ''' Controller for Crawl game'''
    
    def __init__(self):
        self.sock = None
        self.queue = None
        self.state = ControllerState.NotConnected
        self.game_state = GameState()

    def __del__(self):
        self.end_game()

    def start_game(self, username, password):
        self._connect(username, password)
        
        # select species
        menu = self._wait_for_menu('species-main', 3.0)
        if menu is None:
            if self.state == ControllerState.InGame:
                # Crawl has loaded a saved game
                # consume any messages
                while self.read_message():
                    pass
                # end game
                self.end_game()
            raise RuntimeError("Didn't get species menu")
        self.send_input('b') # Minotaur
        
        # select background
        menu = self._wait_for_menu('background-main')
        if menu is None:
            raise RuntimeError("Didn't get background menu")
        self.send_input('h') # Berserker

        # select weapon
        menu = self._wait_for_menu('weapon-main')
        if menu is None:
            raise RuntimeError("Didn't get weapon menu")
        self.send_input('c') # Axe

        msg = self._wait_for_message('map')
        if msg:
            self.state = ControllerState.InGame
    
    def end_game(self):
        self._quit_game()
        self._disconnect()

    def _enqueue_messages(self, timeout=0.5):
        response = self.sock.receive_json(timeout)
        msgs = self._unpack_messages(response)
        for msg in msgs:
            self.queue.put(msg)
    
    def send_message(self, msg):
        self.sock.send_json(msg)

    def read_message(self, timeout=0.5):
        '''Read and return message from Crawl.
           If no messages are received, returns None'''
        if self.queue is None:
            self.queue = Queue()
            
        if self.queue.empty():
            # Ideally, this would be running in a separate thread, but I
            # haven't been able to make it work with the asyncio stuff
            self._enqueue_messages(timeout)
        
        try:
            msg = self.queue.get(block=False)
            self._handle_message(msg)
            return msg
        except Empty:
            return None
    
    def _handle_message(self, msg):
        msg_id = msg['msg']
        if msg_id == 'ping':
            # respond to ping
            self.send_message({'msg':'pong'})
        elif msg_id == 'login_success':
            self.state = ControllerState.LoggedIn
        elif msg_id == 'login_failed':
            self.state = ControllerState.NotLoggedIn
        elif msg_id == 'player':
            if 'species' in msg and msg['species'] == 'Yak':
                # this is a bogus message
                return
            if self.state != ControllerState.InGame:
                logger.info("Game has started")
                self.state = ControllerState.InGame
            parser.update_game_state(msg, self.game_state)
        elif msg_id == 'map':
            if self.state != ControllerState.InGame:
                logger.info("Game has started")
                self.state = ControllerState.InGame
            parser.update_game_state(msg, self.game_state)
    
    def _unpack_messages(self, response):
        '''unpack server response into list of messages'''
        msgs = []
        if response is not None:
            if 'msgs' in response:
                msgs = response['msgs']
            elif 'msg' in response:
                msgs.append(response)
        return msgs
    
    def send_input(self, input_str):
        for c in input_str:
            self.send_message({'msg':'key', 'keycode':ord(c)})
            
    def send_control_input(self, c):
        code = None
        if c >= 'a' and c <= 'z':
            code = ord(c) - ord('a') + 1
        else:
            code = ord(c) - ord('A') + 1
        self.send_message({'msg':'key', 'keycode':code})

    def send_and_receive(self, input_str):
        self.send_input(input_str)
        msg = self.read_message()
        return msg

    def _quit_game(self):
        if self.state == ControllerState.InGame:
            self.state = ControllerState.Quitting
            logger.info('Quitting game...')
            self.send_input(CTRL_Q)
            
            # confirm if prompted
            msg = self._wait_for_message('msgs')
            if msg is not None and 'messages' in msg:
                for message in msg['messages']:
                    if 'Confirm with "yes"' in message['text']:
                        self.send_input('yes\r')

            # dismiss more prompt
            self._wait_for_message('msgs')
            self.send_input(ESC)

            # dismiss inventory menu
            self._wait_for_message('menu')
            self.send_input(ESC)
            
            # dismiss goodbye message
            self._wait_for_message('ui-push')
            self.send_input(ESC)

            # wait for lobby to load
            msg = self._wait_for_message('lobby_complete')
            if msg:
                self.state = ControllerState.Lobby
            else:
                self.state = ControllerState.NotConnected

    @abstractmethod
    def _connect(self, username, password):
        pass

    @abstractmethod
    def _disconnect(self):
        pass
    
    @abstractmethod
    def is_connected(self):
        return False

    def _close_socket(self):
        if self.sock:
            self.sock.close()
            self.sock = None
    
    def _wait_for_message(self, msg_ids, timeout=0.5):
        msg_ids = make_list(msg_ids)
        logger.info("Waiting for message: " + str(msg_ids))
        start = time.time()
        elapsed = 0.0
        while elapsed < timeout:
            msg = self.read_message(timeout-elapsed)
            if msg and msg['msg'] in msg_ids:
                logger.info("Received message: " + msg['msg'])
                return msg
            elapsed = time.time() - start
        return None
    
    def _wait_for_menu(self, menu_ids, timeout=0.5):
        menu_ids = make_list(menu_ids)
        logger.info("Waiting for menu: " + str(menu_ids))
        start = time.time()
        elapsed = 0.0
        while elapsed < timeout:
            msg = self.read_message(timeout)
            if msg and msg['msg'] == 'ui-push' and 'main-items' in msg:
                main_items = msg['main-items']
                if 'menu_id' in main_items and main_items['menu_id'] in menu_ids:
                    # found it
                    logger.info("Received menu: " + main_items['menu_id'])
                    return msg
            elapsed = time.time() - start
        return None

    
class CrawlUnixSocketController(CrawlController):
    
    def __init__(self):
        CrawlController.__init__(self)
        self.crawl_process = None
    
    def _connect(self, username, password = None):
        self._start_crawl(username)
        self._open_socket()
    
    def _disconnect(self):       
        # give crawl a chance to exit gracefully before we kill it
        waited = 0.0
        while self._is_crawl_running() and waited < 5.0:
            time.sleep(0.1)
            waited += 0.1

        self._stop_crawl()       
        self._close_socket()
        
    def is_connected(self):
        # check crawl process is running
        if self.crawl_process and self.crawl_process.poll() is not None:
            return False
        
        svr_sock_path = crawl_socket.UnixSocket.SERVER_SOCKET_PATH
        # check server socket
        if os.path.exists(svr_sock_path):
            # check client socket
            if self.sock and self.sock.open:
                return True
        return False           
        
    def _is_crawl_running(self):
        return (self.crawl_process is not None and self.crawl_process.poll() is None)

    def _get_crawl_exe(self):
        crawl_path = os.getenv('CRAWLDIR')
        if crawl_path is None:
            raise RuntimeError('You must set the CRAWLDIR environment variable with the location of your DCSS installation.')
        crawl_exe = crawl_path + '/bin/crawl'
        crawl_exe_alt = crawl_path + '/crawl'
        if os.path.exists(crawl_exe):
            return crawl_exe
        elif os.path.exists(crawl_exe_alt):
            return crawl_exe_alt
        else:
            raise RuntimeError('Neither ' + crawl_exe + ' nor ' + crawl_exe_alt + ' exist. Have you set the CRAWLDIR environment variable correctly?')

    def _get_crawl_bin_dir(self):
        crawl_path = os.getenv('CRAWLDIR')
        if crawl_path is None:
            raise RuntimeError('You must set the CRAWLDIR environment variable with the location of your DCSS installation.')
        primary = crawl_path + '/bin'
        secondary = crawl_path
        if os.path.exists(primary + '/crawl'):
            return primary
        elif os.path.exists(secondary + '/crawl'):
            return secondary
        else:
            raise RuntimeError('Could not find crawl executable in ' + primary + ' or ' + secondary + '. Have you set the CRAWLDIR environment variable correctly?')

    def _start_crawl(self, username):
        svr_sock_path = crawl_socket.UnixSocket.SERVER_SOCKET_PATH
        
        if os.path.exists(svr_sock_path):
            return
        
        bin_dir = self._get_crawl_bin_dir()
        rcfile = './rcs/' + username + '.rc'
        
        cmd = ['./crawl', '-dir', '.', '-rc', rcfile, '-name', username, '-webtiles-socket', svr_sock_path, '-await-connection']
        logger.info("Starting: " + str(cmd))
        with open("/dev/null", "w") as out:
        #with open("./crawl.out", "w") as out:
            with open('./crawl.err', 'w') as err:
                self.crawl_process = subp.Popen(cmd, cwd = bin_dir, stdout = out, stderr = err, close_fds=True)
        
        # wait for crawl to start
        waited = 0.0
        while not os.path.exists(svr_sock_path) and waited < 5.0:
            time.sleep(0.1)
            waited += 0.1

    def _stop_crawl(self):
        if self._is_crawl_running():
            logger.info('Killing crawl process')
            self.crawl_process.kill() # die horribly
            
            # wait for it to die
            waited = 0.0
            while self._is_crawl_running() and waited < 5.0:
                time.sleep(0.1)
                waited += 0.1
            
            if self._is_crawl_running():
                logger.error("Crawl won't die")
            else:
                logger.info('Crawl process has ended')
        
        # if crawl doesn't exit cleanly it may not clean up its socket properly
        if not self._is_crawl_running():
            svr_sock_path = crawl_socket.UnixSocket.SERVER_SOCKET_PATH
            if os.path.exists(svr_sock_path):
                os.remove(svr_sock_path)
        
        self.crawl_process = None
        
    def _open_socket(self):
        self.sock = crawl_socket.UnixSocket()
        self.sock.open()
        if self.is_connected():
            self.state = ControllerState.Connected
        
        msg = {
            "msg": "attach",
            "primary": True
        }

        self.send_message(msg)
        self.state = ControllerState.LoggedIn

        
class CrawlWebSocketController(CrawlController):
    
    def __init__(self, server_uri):
        CrawlController.__init__(self)
        self.server_uri = server_uri
    
    def _connect(self, username, password):
        self._open_web_socket()
        self._login(username, password)
        self._choose_game()
    
    def _disconnect(self):
        self._close_socket()

    def is_connected(self):
        return (self.sock and self.sock.open)
        
    def _open_web_socket(self):
        self.sock = crawl_socket.WebSocket(self.server_uri)
        self.sock.open()
        if self.is_connected():
            self.state = ControllerState.Connected
    
    def _login(self, username, password):
        self._wait_for_message('lobby_complete')
        
        login_msg = {
            'msg':'login',
            'username':username,
            'password':password
        }
        self.send_message(login_msg)
        
        msg = self._wait_for_message(['login_success', 'login_fail'])
        if msg is None or msg['msg'] == 'login_fail':
            logger.critical("Login failed")
            raise RuntimeError("Login failed")
        
        msg = self._wait_for_message('set_game_links')
        if not msg:   
            logger.critical("Didn't receive game links")
            raise RuntimeError("Didn't receive game links")
        self.state = ControllerState.Lobby   
    
    def _choose_game(self):
        if self.state == ControllerState.Lobby:
            self.state = ControllerState.StartingGame
            choose_game_msg = {'msg':'play', 'game_id':'dcss-web-trunk'}
            self.send_message(choose_game_msg)
