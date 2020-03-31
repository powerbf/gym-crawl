'''
Gym environment for crawl socket version
'''

import logging

import gym

from ..crawl_controller import CrawlUnixSocketController, CrawlWebSocketController


logger = logging.getLogger('crawl-socket-env')


class CrawlSocketEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
    
        self.controller = None

        self.character_name = 'Bot'
        self.password = 'Test'
        
        self.server_uri = None
        
        self.steps = 0
    
    def __del__(self):
        print("CrawlSocketEnv destructor")
        self.close()
    
    def set_character_name(self, value):
        self.character_name = value

    def get_character_name(self):
        return self.character_name
    
    def set_password(self, value):
        '''Set password for logging into web server'''
        self.password = value

    def set_server_uri(self, value):
        '''Set web server URI'''
        self.server_uri = value

    def reset(self):
        logger.info('reset')
        
        self._end_game()
        self._start_game()
        
        self.steps = 0
        self.num_times_pressed_enter = 0
        
    def step(self, action):
        logger.info('step')
        msg = self.controller.send_and_receive(action)
        self.steps += 1
        return None, 0, False, msg
        
    def close(self):
        self._end_game()
    
    def _start_game(self):
        if self.server_uri:
            self.controller = CrawlWebSocketController(self.server_uri)
        else:
            self.controller = CrawlUnixSocketController()
        self.controller.start_game(self.character_name, self.password)
    
    def _end_game(self):
        if self.controller:
            self.controller.end_game()
            self.controller = None
